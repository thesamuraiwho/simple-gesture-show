import requests
import os
from os.path import join, dirname
from dotenv import load_dotenv
from PIL import Image
import pprint

pp = pprint.PrettyPrinter(indent=4)

# Reference for help with python-dotenv by Will: https://stackoverflow.com/questions/41546883/what-is-the-use-of-python-dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

print(f"Pexels API Key: {PEXELS_API_KEY[0:3]}")

# baseurl = 'https://api.pexels.com/v1/'
auth = {'Authorization': PEXELS_API_KEY}


# req = requests.get(baseurl + "search?query=people", auth=auth)
req = requests.get("https://api.pexels.com/v1/search?query=people", headers=auth, stream=True)

print(req.text)
print(type(req.text))
print(req.json())
print(type(req.json()))
print(req.json()['photos'])
print("\n\n\n\n\n\n")
print(req.json()['photos'][0])
img_url = req.json()['photos'][0]['src']['original'] # issue displaying original image but large appears to work for some images

# Help streaming images into pillow via URL by Giovanni Cappellotto: https://stackoverflow.com/questions/7391945/how-do-i-read-image-data-from-a-url-in-python
i = Image.open(requests.get(img_url, stream=True).raw)

# Help showing pillow images by martineau: https://stackoverflow.com/questions/12570859/how-to-show-pil-images-on-the-screen/12571366
i.show()


# Working with Pexels Collections

# req = requests.get("https://api.pexels.com/v1/collections/4m8at5r?per_page=1", headers=auth, stream=True)
req = requests.get("https://api.pexels.com/v1/collections/4m8at5r", headers=auth, stream=True)

print(req.json())
pp.pprint(req.json())
collection_media = req.json()['media']
for photo in collection_media:
    i = Image.open(requests.get(photo['src']['original'], stream=True).raw)
    i.show()
