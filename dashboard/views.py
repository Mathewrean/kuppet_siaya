from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from accounts.models import BBFContribution, SupportTicket
from core.models import FinancialStatement


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
