To run the flask web service on gunicorn
    Navigate to the web service folder using the following command.
        cd C:\FinalProjectFolder\solution\WeatherSvc
        
    Use the Dockerfile to build the docker image using the following command
        docker  buildx build -t weathersvc .
        
    Run the docker container with the newly created docker image
        docker run --rm -it -p 8080:80  --name weathersvc-container weathersvc
        
    You can confirm that the file runs by visiting http://localhost:8080/ on a browser
    You can then navigate to the following pages
        http://localhost:8080/directions
        http://localhost:8080/directions/4
        http://localhost:8080/stations
        http://localhost:8080/measurements

To run the flask web service on azurecr
    Create a new web service
        Create a resource group
            az group create --name <my-rg> --location "UK South"
        Create an app service plan
            az appservice plan create --name <my-app-service-plan> --resource-group <my-rg> --sku FREE
        Create a web app    
            az webapp create --name <app-name> --resource-group <my-rg> --plan <my-plan> --runtime "python|3.9"
        
    To push to Azure container registry
        On Azure CLI
            login   
                run az login
            create a new resource group
                az group create --name myResourceGroup --location uksouth
            create a new registry   
                az acr create --resource-group myResourceGroup --name mycontainerregistry --sku Basic
                Take note of the loginServer from the output which is the fully qualified <registry-name>
            Login to the registry   
                az acr login --name <registry-name>
            Pull the image from DockerHub
                docker pull <your docker repo>/weathersvc:v1
            Tag the docker image with a microsoft tag
                docker tag <your docker repo>/weathersvc:v1 <registry-name>/weathersvc:v1
            Push image to registry
                docker push crprb21192cs456projectcontainerregistry.azurecr.io/weathersvc:v1
                docker push <registry-name>/weathersvc:v1
    
    To deploy the container to the web app
        I had to do this via the Azure portal
        Create new web app
            Supply resource-group, name, region, and service plans
            Choose Container as the publishing option
        Select container
            Choose Azure Container Registry
            manually add the image name and tag
        Allow public access
        Create