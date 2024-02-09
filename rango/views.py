from django.shortcuts import render
from django.http import HttpResponse
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from django.shortcuts import redirect
from django.urls import reverse
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime


def index(request):
    #Query the database for the list of All categories currently stored
    #Order the categories by the number of likes in descending order
    #Retrieve the top 5 only -- or all if less than 5
    #Place the list in our context_dict dictionary (with our boldmessage)
    #that will be passed to the template engine
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]
    
    #Construct a dictionary to pass to the template engine as its context.
    #Note the key boldmessage matches to {{ boldmessage }} in the template!
    context_dict = {}
    context_dict= {'boldmessage': 'Crunchy, creamy, cookie, candy, cupcake!'}
    context_dict['categories'] = category_list
    context_dict['pages'] = page_list
    
    visitor_cookie_handler(request)
    
    #Return a rendered response to send to the client
    #We make use of the shortcut function to make our lives easier.
    #Note that the first parameter is the template we wish to use.
    #Obtain our Response object early so we can add cookie information
    return render(request, 'rango/index.html', context=context_dict)


def about(request):
    context_dict = {'boldmessage': 'This tutorial has been put together by Hammaad Uddin'}

    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']

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

@login_required
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

@login_required
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
                return redirect(reverse('rango:show_category', kwargs={'category_name_slug': category_name_slug}))
        else:
            print(form.errors)
    context_dict = {'form': form, 'category': category}
    return render(request, 'rango/add_page.html', context=context_dict)

def register(request):
    #A boolean value for telling the template
    #whether the registration was successful.
    #Set to False initially. Code changes value to
    #True when registration succeeds.
    registered = False

    #if its a HTTP POST, were interested in processing form data.
    if request.method == 'POST':
        #Attempt to grab information from the raw form infromation
        #Note that we make use of both UserForm and UserProfileFrom
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        #If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            #save the user's form data to the database.
            user = user_form.save()

            #Now we hash the password with the set_password method.
            #Once hashed, we can update the user object
            user.set_password(user.password)
            user.save()

            #Now sort out the UserProfile instance.
            #Since we need to set the user attribute ourselves,
            #we set commit=False. This delays saving the model
            #untill we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            #Did the user provide a profile picture?
            #If so, we need to get it from the input form and
            #put it in the UserProfile model
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            #Now we save the UserProfile model instance
            profile.save()

            #update our variable to indicate that the template 
            #registration was successful
            registered = True
        else:
            #Invalid form or forms - mistakes or something else?
            #Print problems to the terminal.
            print(user_form.errors, profile_form.errors)
        
    else:
        #Not a HTTP POST, so we render our form using two ModelForm instances
        #These forms will be blank, ready for user input.
        user_form = UserForm()
        profile_form = UserProfileForm()
    
    #Render the template depending on the context.
    return render(request,
                  'rango/register.html',
                  context = {'user_form': user_form,
                             'profile_form': profile_form,
                             'registered': registered})

def user_login(request):
    #if the request is a HTTP POST, try to pull out the relevant information
    if request.method == 'POST':
        #gather the username and password provided by the user
        #This information is obtained from the login form
        #we use request.POST.get('<variable>') as opposed
        #to request.POST['<variable>'], because the 
        #request.POST.get('<variable>') returns None if the
        #value does not exist, while request.POST['<variable>']
        #will raise a KeyError exception
        username = request.POST.get('username')
        password = request.POST.get('password')

        #Use Django's machinery to attempt to see if the username/password
        #combination is valid - a User object is returned if it is
        user = authenticate(username=username, password=password)

        #if we have a User object, the details are correct.
        #if None (Python's way of representing the absence of a value), no user
        #with matching credentials was found
        if user:
            #is the account active? It could have been disabled
            if user.is_active:
                #if the account is valid and active, we can log the user in
                #well send the user back to the homepage
                login(request, user)
                return redirect(reverse('rango:index'))
            else:
                #An inacive account was used - no logging in!
                return HttpResponse("Your Rango account is disabled")
        else:
            #Bad login details were provided. So we cant log the user in
            print(f"Invalid login details: {username}, {password}")
            return HttpResponse("Invalid login details supplied.")
        
    #The request is not a HTTP POST, so display the login form
    #This scenario would most likely be a HTTP GET
    else:
        #No context variable to pass to the template system,, hence the
        #blank dictionary object...
        return render(request, 'rango/login.html')
    
@login_required
def restricted(request):
    return render(request, 'rango/restricted.html')


#Use the login_required() decorator to ensure only those logged in can
#access the view
@login_required
def user_logout(request):
    #since we know the user is logged in, we can now just log them out.
    logout(request)
    #take the user back to the homepage
    return redirect(reverse('rango:index'))

#A helper method
def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val

def visitor_cookie_handler(request):
    #get the number of visits to the site
    #we use the COOKIES.get() function to obtain the visits cookie.
    #if the cookie exists, the value returned is casted to an integer
    #if the cookie doesnt exist, then the default value of 1 is used
    visits = int(get_server_side_cookie(request, 'visits', '1'))

    last_visit_cookie = get_server_side_cookie(request, 'last_visit', str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7],
                                        '%Y-%m-%d %H:%M:%S')
    
    #if its been more than a day since the last visit...
    if (datetime.now() - last_visit_time).days > 0:
        visits = visits + 1 
        #Update the last visit cookie now that we have updated the count
        request.session['last_visit'] = str(datetime.now())
    else:
        #Set the last visit cookie
        request.session['last_visit']= last_visit_cookie

    #Update/set the visits cookie
    request.session['visits'] = visits