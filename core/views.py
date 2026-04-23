from django.core.paginator import Paginator
from .models import NewsPost, GalleryAlbum, ContactMessage, BECMember, BGCMember

def home(request):
    news = NewsPost.objects.filter(is_published=True).order_by('-published_date')[:6]
    albums = GalleryAlbum.objects.all()[:5]  # For slider
    return render(request, 'core/home.html', {'news': news, 'albums': albums})

def about(request):
    return render(request, 'core/about.html')

def about_profile(request):
    return render(request, 'core/about_profile.html')

def about_bec(request):
    members = BECMember.objects.all()
    return render(request, 'core/about_bec.html', {'members': members})

def about_bgc(request):
    members = BGCMember.objects.all()
    return render(request, 'core/about_bgc.html', {'members': members})

def projects(request):
    return render(request, 'core/projects.html')

def projects_bbf(request):
    return render(request, 'core/projects_bbf.html')

def projects_bus(request):
    return render(request, 'core/projects_bus.html')

def projects_center(request):
    return render(request, 'core/projects_center.html')

def gallery(request):
    albums = GalleryAlbum.objects.all()
    return render(request, 'core/gallery.html', {'albums': albums})

def contact(request):
    if request.method == 'POST':
        ContactMessage.objects.create(
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            email=request.POST['email'],
            tsc_number=request.POST.get('tsc_number', ''),
            phone_number=request.POST.get('phone_number', ''),
            subject=request.POST['subject'],
            message=request.POST['message'],
            consent=request.POST.get('consent') == 'on'
        )
        messages.success(request, 'Your message has been sent successfully!')
        return redirect('contact')
    return render(request, 'core/contact.html')

def news_detail(request, slug):
    post = get_object_or_404(NewsPost, slug=slug, is_published=True)
    return render(request, 'core/news_detail.html', {'post': post})

def news_archive(request):
    category = request.GET.get('category')
    search = request.GET.get('search')
    
    news = NewsPost.objects.filter(is_published=True).order_by('-published_date')
    
    if category:
        news = news.filter(category=category)
    
    if search:
        news = news.filter(title__icontains=search) | news.filter(story__icontains=search)
    
    paginator = Paginator(news, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'core/news_archive.html', {'page_obj': page_obj, 'category': category, 'search': search})
