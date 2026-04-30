from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from rest_framework.permissions import IsAuthenticated

from accounts.models import BBFContribution, SupportTicket, CustomUser
from core.models import FinancialStatement
from bbf.models import BBFClaim, BBFBeneficiary
from bbf.serializers import BBFClaimSerializer
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


# =============================================================================
# Subcounty Representative Views (Dashboard)
# =============================================================================

class SubcountyDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/subcounty_dashboard.html"
    login_url = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_subcounty_rep or request.user.is_superuser):
            from django.contrib import messages
            messages.error(request, "Access denied. Subcounty Representative role required.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class SubcountyClaimReviewView(LoginRequiredMixin, DetailView):
    template_name = "dashboard/subcounty_claim_review.html"
    login_url = reverse_lazy("login")
    model = BBFClaim

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_subcounty_rep or request.user.is_superuser):
            from django.contrib import messages
            messages.error(request, "Access denied. Subcounty Representative role required.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return BBFClaim.objects.filter(status='awaiting_subcounty')


# =============================================================================
# County Representative Views (Dashboard)
# =============================================================================

class CountyDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/county_dashboard.html"
    login_url = reverse_lazy("login")

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_county_rep or request.user.is_superuser):
            from django.contrib import messages
            messages.error(request, "Access denied. County Representative role required.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class CountyClaimReviewView(LoginRequiredMixin, DetailView):
    template_name = "dashboard/county_claim_review.html"
    login_url = reverse_lazy("login")
    model = BBFClaim

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_county_rep or request.user.is_superuser):
            from django.contrib import messages
            messages.error(request, "Access denied. County Representative role required.")
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return BBFClaim.objects.filter(status='awaiting_county')