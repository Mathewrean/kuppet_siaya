from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from accounts.models import BBFContribution
from core.models import FinancialStatement

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # BBF Status logic
        contributions = BBFContribution.objects.filter(user=user).order_by('-contribution_date')
        total_contributed = sum(c.amount for c in contributions)
        # Assume required is 5000 or something
        context['bbf_status'] = 'Good Standing' if total_contributed >= 5000 else 'Pending Arrears'
        context['contributions'] = contributions[:5]
        context['financial_statements'] = FinancialStatement.objects.all().order_by('-fiscal_year')
        return context

class BBFStatusView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/bbf_status.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        contributions = BBFContribution.objects.filter(user=user).order_by('-contribution_date')
        context['contributions'] = contributions
        return context

class FinancialsView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/financials.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['financial_statements'] = FinancialStatement.objects.all().order_by('-fiscal_year')
        return context

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/profile.html'
    login_url = reverse_lazy('login')

class SupportView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/support.html'
    login_url = reverse_lazy('login')
