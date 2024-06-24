from seleniumwire import webdriver

# Create a new instance of the Selenium Wire WebDriver
driver = webdriver.Chrome()


# Define a request interceptor function
def my_request_interceptor(request):
    # Do something with the intercepted request
    print(f"Intercepted request: {request.url}")


# Define a response interceptor function
def my_response_interceptor(request, response):
    # Do something with the intercepted response
    print(f"Intercepted response: {response.status_code}")


# Set the request interceptor
driver.request_interceptor = my_request_interceptor

# Set the response interceptor
driver.response_interceptor = my_response_interceptor

# Make requests
# driver.get('https://www.example.com')
driver.get('https://www.google.com')

# Close the driver
driver.quit()