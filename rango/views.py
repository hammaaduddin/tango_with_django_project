from django.shortcuts import render
from django.http import HttpResponse
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from django.shortcuts import redirect
from rango.forms import PageForm
from django.urls import reverse

def index(request):
    #Query the database for the list of All categories currently stored
    #Order the categories by the number of likes in descending order
    #Retrieve the top 5 only -- or all if less than 5
    #Place the list in our context_dict dictionary (with our boldmessage)
    #that will be passed to the template engine

    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]

    context_dict = {}
    #Construct a dictionary to pass to the template engine as its context.
    #Note the key boldmessage matches to {{ boldmessage }} in the template!

    context_dict= {'boldmessage': 'Crunchy, creamy, cookie, candy, cupcake!'}
    context_dict['categories'] = category_list
    context_dict['pages'] = page_list
    
    #Return a rendered response to send to the client
    #We make use of the shortcut function to make our lives easier.
    #Note that the first parameter is the template we wish to use.
    return render(request, 'rango/index.html', context=context_dict)

def about(request):
    context_dict = {'boldmessage': 'This tutorial has been put together by Hammaad Uddin'}

    return render(request, 'rango/about.html', context=context_dict)

def show_category(request, category_name_slug):
    #create a context dictionary which we can pass
    #to the template rendering engin
    context_dict = {}

    try:
        #can we find a category name slug with the given name?
        #if we cant, the .get() method raises a DoesNotExist exception
        #the .get() method returns one model instance or raises an exception
        category = Category.objects.get(slug=category_name_slug)

        #retrieve all of the associated pages
        #the filter() will return a list of page objects or an empty list.
        pages = Page.objects.filter(category=category)

        #adds our results list to the template context under name pages.
        context_dict['pages'] = pages

        #We also add the category object from
        #the database to the context dictionary
        #well use this in the template to verify that the category exists
        context_dict['category'] = category
    except Category.DoesNotExist:
        #we get here if we didnt find the specified category
        #dont do anything -
        #the template will display the 'no category' message for us
        context_dict['pages'] = None
        context_dict['category'] = None
    
    #Go render the response and return it to the client
    return render(request, 'rango/category.html', context=context_dict)

def add_category(request):
    form = CategoryForm()

    #A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        #have we been provided with a valid form?
        if form.is_valid():
            #Save the new category to the database
            form.save(commit=True)
            #Now that the category is save, we could confirm this
            #For now, just redirect the user back to the index view.
            return redirect('/rango/')
        else:
            #The supplied form contains errors - 
            #just print them to the terminal
            print(form.errors)

    # Will handle the bad form, new form, or no form supplied cases.
    # Render the form with error messages (if any).
    return render(request, 'rango/add_category.html', {'form': form})

def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category = None

    # You cannot add a page to a Category that does not exist...
    if category is None:
        return redirect('/rango/')

    form = PageForm()

    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()
                return redirect(reverse('rango:show_category',
                                        kwargs={'category_name_slug':
                                                category_name_slug}))
        else:
            print(form.errors)
    context_dict = {'form': form, 'category': category}
    return render(request, 'rango/add_page.html', context=context_dict)