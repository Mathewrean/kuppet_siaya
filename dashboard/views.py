from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django.http import HttpResponseRedirect, JsonResponse
from rest_framework.permissions import IsAuthenticated

from accounts.models import BBFContribution, SupportTicket, CustomUser
from core.models import FinancialStatement
from bbf.models import BBFClaim, BBFBeneficiary, BBFClaimDocument
from bbf.serializers import BBFClaimSerializer, BBFBeneficiaryCreateSerializer
from bbf.views import create_notification
import json


def get_bbf_status(total_contributed):
    if total_contributed >= 5000:
        return "Good Standing"
    if total_contributed > 0:
        return "Pending Arrears"
    return "Lapsed"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"
    login_url = reverse_lazy("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        contributions = BBFContribution.objects.filter(user=user).order_by("-contribution_date")
        total_contributed = sum(contribution.amount for contribution in contributions)

        context["bbf_status"] = get_bbf_status(total_contributed)
        context["contributions"] = contributions[:5]
        context["financial_statements"] = FinancialStatement.objects.all().order_by("-fiscal_year")[:5]
        context["member_first_name"] = user.first_name or user.get_full_name() or user.tsc_number
        return context


class BBFStatusView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/bbf_status.html"
    login_url = reverse_lazy("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        contributions = BBFContribution.objects.filter(user=user).order_by("-contribution_date")
        total_contributed = sum(contribution.amount for contribution in contributions)
        context["contributions"] = contributions
        context["bbf_status"] = get_bbf_status(total_contributed)
        return context


class FinancialsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/financials.html"
    login_url = reverse_lazy("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_statements = FinancialStatement.objects.all().order_by("-fiscal_year", "-uploaded_at")
        years = list(all_statements.values_list("fiscal_year", flat=True).distinct())
        selected_year = self.request.GET.get("year", "")
        statements = all_statements.filter(fiscal_year=selected_year) if selected_year else all_statements

        context["financial_statements"] = statements
        context["years"] = years
        context["selected_year"] = selected_year
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/profile.html"
    login_url = reverse_lazy("login")

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email", "").strip() or None
        phone_number = request.POST.get("phone_number", request.user.phone_number)

        if email and type(request.user).objects.exclude(pk=request.user.pk).filter(email__iexact=email).exists():
            messages.error(request, "That email address is already in use.")
            return redirect("profile")

        request.user.email = email
        request.user.phone_number = phone_number
        request.user.save(update_fields=["email", "phone_number"])
        messages.success(request, "Your profile has been updated.")
        return redirect("profile")


class SupportView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/support.html"
    login_url = reverse_lazy("login")

    def post(self, request, *args, **kwargs):
        SupportTicket.objects.create(
            user=request.user,
            subject=request.POST["subject"],
            message=request.POST["message"],
        )
        messages.success(request, "Your support request has been submitted.")
        return redirect("support")


# =============================================================================
# BBF Claims - Member Views
# =============================================================================

class BBFClaimsListView(LoginRequiredMixin, ListView):
    template_name = "dashboard/bbf_claims_list.html"
    login_url = reverse_lazy("login")
    context_object_name = "claims"

    def get_queryset(self):
        return BBFClaim.objects.filter(member=self.request.user).order_by("-submitted_at")


class BBFClaimDetailView(LoginRequiredMixin, DetailView):
    template_name = "dashboard/bbf_claim_detail.html"
    login_url = reverse_lazy("login")
    model = BBFClaim

    def get_queryset(self):
        return BBFClaim.objects.filter(member=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['beneficiary_type_choices'] = BBFBeneficiary.BENEFICIARY_TYPE_CHOICES
        return context


class BBFClaimCreateView(LoginRequiredMixin, CreateView):
    template_name = "dashboard/bbf_claim_new.html"
    login_url = reverse_lazy("login")
    model = BBFClaim
    fields = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['beneficiary_type_choices'] = BBFBeneficiary.BENEFICIARY_TYPE_CHOICES
        context["member_document_types"] = BBFClaimDocument.DOCUMENT_TYPE_CHOICES
        return context

    def form_valid(self, form):
        # Set member and initial status before saving
        form.instance.member = self.request.user
        form.instance.status = 'pending'
        form.instance.submitted_at = timezone.now()
        return super().form_valid(form)

    def get_success_url(self):
        from django.urls import reverse
        return reverse('bbf_claims')

    def post(self, request, *args, **kwargs):
        # Handle claim creation with beneficiaries AND member documents via JavaScript FormData
        # Parse beneficiaries from request.POST and request.FILES
        # Expected format: beneficiaries-{index}-type, beneficiaries-{index}-name, beneficiaries-{index}-document
        # Also: member_doc_{doc_type} for member documents
        from django.http import JsonResponse
        from django.urls import reverse
        from django.contrib import messages
        
        beneficiaries_data = {}
        for key, value in request.POST.items():
            if key.startswith('beneficiaries-'):
                parts = key.split('-')
                if len(parts) == 3:
                    idx, field = parts[1], parts[2]
                    if field == 'type':
                        field = 'beneficiary_type'
                    elif field == 'name':
                        field = 'full_name'
                    if idx not in beneficiaries_data:
                        beneficiaries_data[idx] = {}
                    beneficiaries_data[idx][field] = value
        
        # Handle file uploads - separate beneficiary files and member files
        member_doc_files = {}
        for key, uploaded_file in request.FILES.items():
            if key.startswith('beneficiaries-'):
                parts = key.split('-')
                if len(parts) == 3:
                    idx, field = parts[1], parts[2]
                    if field == 'type':
                        field = 'beneficiary_type'
                    elif field == 'name':
                        field = 'full_name'
                    if idx not in beneficiaries_data:
                        beneficiaries_data[idx] = {}
                    beneficiaries_data[idx][field] = uploaded_file
            elif key.startswith('member_doc_'):
                doc_type = key.replace('member_doc_', '')
                member_doc_files[doc_type] = uploaded_file
        
        # Convert to list sorted by index
        sorted_indices = sorted(beneficiaries_data.keys(), key=int)
        beneficiaries_list = [beneficiaries_data[idx] for idx in sorted_indices]
        
        # Validate member documents
        required_member_doc_types = [doc_type for doc_type, _ in BBFClaimDocument.DOCUMENT_TYPE_CHOICES]
        missing_member_docs = []
        required_name_map = dict(BBFClaimDocument.DOCUMENT_TYPE_CHOICES)
        for doc_type in required_member_doc_types:
            if doc_type not in member_doc_files or not member_doc_files[doc_type]:
                missing_member_docs.append(required_name_map[doc_type])
        
        if missing_member_docs:
            msg = 'Missing member documents: ' + ', '.join(missing_member_docs)
            messages.error(request, msg)
            return JsonResponse({'error': msg, 'missing_documents': missing_member_docs}, status=400)
        
        # Validate beneficiary documents
        if not beneficiaries_list:
            msg = 'At least one beneficiary with document is required'
            messages.error(request, msg)
            return JsonResponse({'error': msg}, status=400)
        
        has_document = False
        for ben_data in beneficiaries_list:
            if 'document' in ben_data and ben_data['document']:
                if ben_data['document'].size > 5 * 1024 * 1024:
                    msg = f'File size exceeds 5MB for {ben_data.get("full_name", "beneficiary")}.'
                    messages.error(request, msg)
                    return JsonResponse({'error': msg}, status=400)
                has_document = True
        
        if not has_document:
            msg = 'At least one beneficiary must have a document uploaded.'
            messages.error(request, msg)
            return JsonResponse({'error': msg}, status=400)
        
        # Validate member document file types and sizes
        for doc_type, file in member_doc_files.items():
            if file.size > 5 * 1024 * 1024:
                msg = f'File size exceeds 5MB for {doc_type}.'
                messages.error(request, msg)
                return JsonResponse({'error': msg}, status=400)
            allowed = ['application/pdf', 'image/jpeg', 'image/png']
            if file.content_type not in allowed:
                msg = f'Invalid file type for {doc_type}. Allowed: PDF, JPG, PNG'
                messages.error(request, msg)
                return JsonResponse({'error': msg}, status=400)
        
        # Create claim
        claim = BBFClaim(member=request.user, status='pending')
        claim.save()
        
        # Create member claim documents
        for doc_type, file in member_doc_files.items():
            BBFClaimDocument.objects.create(
                claim=claim,
                document_type=doc_type,
                file=file,
                status='pending',
                is_verified=False
            )
        
        # Create beneficiaries
        created_beneficiaries = []
        errors = []
        for ben_data in beneficiaries_list:
            serializer = BBFBeneficiaryCreateSerializer(
                data=ben_data,
                context={'claim': claim}
            )
            try:
                if serializer.is_valid(raise_exception=True):
                    beneficiary = serializer.save()
                    created_beneficiaries.append(beneficiary)
            except Exception as e:
                errors.append(str(e))
        
        if errors or not created_beneficiaries:
            claim.delete()
            for error in errors:
                messages.error(request, error)
            return JsonResponse({'error': errors}, status=400)
        
        # Submit the claim (set status)
        claim.status = 'awaiting_subcounty'
        claim.save()
        
        # Notification
        create_notification(
            request.user,
            'BBF Claim Submitted',
            f'Your BBF claim {claim.claim_reference} has been submitted.',
            claim
        )
        
        messages.success(request, f'Claim {claim.claim_reference} submitted successfully.')
        return JsonResponse({'id': claim.id, 'redirect_url': reverse('bbf_claim_detail', kwargs={'pk': claim.id})})



# =============================================================================
# Subcounty Representative Views (Dashboard)
# =============================================================================

class SubcountyDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/subcounty_dashboard.html"
    login_url = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_subcounty_rep or request.user.is_superuser):
            from django.contrib import messages
            messages.error(request, "Access denied. Subcounty Representative role required.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class SubcountyClaimReviewView(LoginRequiredMixin, DetailView):
    template_name = "dashboard/subcounty_claim_review.html"
    login_url = reverse_lazy("login")
    model = BBFClaim

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_subcounty_rep or request.user.is_superuser):
            from django.contrib import messages
            messages.error(request, "Access denied. Subcounty Representative role required.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = BBFClaim.objects.filter(status='awaiting_subcounty')
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(member__sub_county=self.request.user.sub_county)


# =============================================================================
# County Representative Views (Dashboard)
# =============================================================================

class CountyDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/county_dashboard.html"
    login_url = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_county_rep or request.user.is_superuser):
            from django.contrib import messages
            messages.error(request, "Access denied. County Representative role required.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class CountyClaimReviewView(LoginRequiredMixin, DetailView):
    template_name = "dashboard/county_claim_review.html"
    login_url = reverse_lazy("login")
    model = BBFClaim

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_county_rep or request.user.is_superuser):
            from django.contrib import messages
            messages.error(request, "Access denied. County Representative role required.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return BBFClaim.objects.filter(status='awaiting_county')
