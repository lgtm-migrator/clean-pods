import requests
import json
import os, sys
from datetime import timedelta, datetime

# --- Variables ---------------------------------------------------------------
# Get the token for authenticate via the API
if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount"):
    token = open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r").read().replace('\n', '')
else:
    token = os.environ["TOKEN"]

# API URL. Ex. https://kubernetes.default.svc/api/
apiURL = os.environ["API_URL"]

# Namespace where the pods are running
namespace = os.environ.get("NAMESPACE", "gitlab")

# Expiration time in hours, the pods older than "maxHours" are going to be deleted
maxHours = int(os.environ.get("MAX_HOURS", "1"))

# Only pods with the following status are going to be deleted
# You can send a list of string separate by comma, Ex. "Pending, Running, Succeeded, Failed, Unknown"
podStatus = os.environ["POD_STATUS"].replace(' ','').split(",")

# --- Functions ---------------------------------------------------------------
def callAPI(method, url):
    headers = {"Authorization": "Bearer "+token}
    requests.packages.urllib3.disable_warnings()
    request = requests.request(method, url, headers=headers, verify=False)
    return request.json()

def getPods(namespace):
    url = apiURL+"api/v1/namespaces/"+namespace+"/pods"
    response = callAPI('GET', url)
    return response["items"]

def deletePod(podName, namespace):
    url = apiURL+"api/v1/namespaces/"+namespace+"/pods/"+podName
    response = callAPI('DELETE', url)
    print("Delete call => %s" % url)
    return response

# --- Main --------------------------------------------------------------------
# Get all pods running in a namespace and delete older than "maxHours"
pods = getPods(namespace)
if not pods:
    print("No pods for delete.")

for pod in pods:
    print("%s" % json.dumps(pod), file=sys.stderr)
    if pod["metadata"]["name"].startswith(os.environ["STARTS_WITH"]):
        print("To delete pod name %s" % pod["metadata"]["name"])
        if pod["status"]["phase"] in podStatus:
            podStartTime = datetime.strptime(pod["status"]["startTime"], "%Y-%m-%dT%H:%M:%SZ")
            nowDate = datetime.now()
            print("Now: %s" % str(nowDate))
            if ((podStartTime + timedelta(hours=maxHours)) < nowDate):
                print("Deleting pod ("+pod["metadata"]["name"]+"). Status ("+pod["status"]["phase"]+"). Start time ("+str(podStartTime)+")")
                deletePod(pod["metadata"]["name"], namespace)
