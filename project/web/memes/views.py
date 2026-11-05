from datetime import timedelta

from django.contrib import messages
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import MemeTemplateForm
from .models import GenerationActivity, MemeTemplate


def dashboard(request):
    if request.method == "POST":
        if request.POST.get("action") == "add_template":
            form = MemeTemplateForm(request.POST, request.FILES)
            if form.is_valid():
                template = form.save()
                messages.success(request, f"Заготовка «{template.title}» сохранена.")
                return redirect(f"{request.path}?selected={template.pk}")
        elif request.POST.get("action") == "generate":
            template = get_object_or_404(MemeTemplate, pk=request.POST.get("template_id"))
            today = timezone.localdate()
            activity, _ = GenerationActivity.objects.get_or_create(activity_date=today)
            GenerationActivity.objects.filter(pk=activity.pk).update(generation_count=F("generation_count") + 1)
            messages.success(request, f"Мем по заготовке «{template.title}» создан.")
            return redirect(f"{request.path}?selected={template.pk}")
    else:
        form = MemeTemplateForm()

    templates = MemeTemplate.objects.all()
    selected = templates.filter(pk=request.GET.get("selected")).first() if request.GET.get("selected") else None
    selected = selected or templates.first()
    today = timezone.localdate()
    start_date = today - timedelta(days=6)
    counts_by_date = {
        item.activity_date: item.generation_count
        for item in GenerationActivity.objects.filter(activity_date__range=(start_date, today))
    }
    max_count = max(counts_by_date.values(), default=0)
    chart = [
        {
            "date": start_date + timedelta(days=offset),
            "count": counts_by_date.get(start_date + timedelta(days=offset), 0),
            "percent": round(counts_by_date.get(start_date + timedelta(days=offset), 0) / max_count * 100) if max_count else 2,
        }
        for offset in range(7)
    ]
    weekly_total = sum(counts_by_date.values())
    return render(
        request,
        "memes/dashboard.html",
        {"form": form, "templates": templates, "selected": selected, "chart": chart, "weekly_total": weekly_total},
    )