from django.shortcuts import render
from .models import SearchResult
from django.db.models import Q

def home(request):
    return render(request, 'index.html')

def results(request):
    query = request.GET.get('q', '').strip()
    
    # Aapke Database wale results (Flipkart/Social Style ke liye)
    if query:
        db_results = SearchResult.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    else:
        db_results = SearchResult.objects.all()

    return render(request, 'results.html', {'results': db_results, 'query': query})
