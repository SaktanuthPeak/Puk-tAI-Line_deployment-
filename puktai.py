from __future__ import unicode_literals

import errno
import os
import sys
import tempfile
from dotenv import load_dotenv

from flask import Flask, request, abort, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import (
    MessageEvent, ImageMessage, TextSendMessage, ImageSendMessage
)

from PIL import Image
import torch
import torchvision.models as models
import torchvision.transforms as transforms

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)

load_dotenv()

line_bot_api = LineBotApi('1SHNU1gA9eO02b4ijaoKNsk1z+5UjpCSUwWjGVQ5jCDe4vjpjNDSPTIHTlSlAQeJ99ewuDWM5H1Ltvw40LJmf7aDaWHjHP/ibc/x9I8TlzmOJy/9VzQFo7Xb0ZADLZ8cfp7ppDw1RHTcpSFB4JGugQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('948d8ef47eaa6a78a417767c8477a90c')

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

# Load the ResNet-34 model
model = models.resnet34()
num_features = model.fc.in_features
model.fc = torch.nn.Linear(num_features, 18)  
model.load_state_dict(torch.load("Southern.pth", map_location=torch.device('cpu')))
model.eval()
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)

    return 'OK'


# Preprocess function for image classification
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Define class labels
class_labels = [
"ไก่ต้มขมิ้น",
 "เเกงคั่วหอยขมใบชะพลู",
 "ขนมจีนนํ้ายาปู",
 "ไก่กอเเละ",
 "ไก่ทอดหาดใหญ่",
 "ไข่ครอบ",
 "ข้าวยํา",
 "คั่วกลิ้งหมู",
 "ใบเหลียงต้มกะทิกุ้งสด",
 "หมูฮ้อง",
 "นํ้าพริกกะปิ",
 "นํ้าพริกกุ้งเสียบ",
 "ปลากรายทอดขมิ้น",
 "เเกงเหลืองปลากระพง",
 "ใบเหลียงผัดไข่",
 "หมูผัดกะปิ",
 "สะตอผัดกุ้ง",
 "เเกงไตปลา",
]

# ... (other code)

@handler.add(MessageEvent, message=(ImageMessage))
def handle_content_message(event):
    if isinstance(event.message, ImageMessage):
        ext = 'jpg'
    else:
        return

    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '.' + ext
    os.rename(tempfile_path, dist_path)

    im = Image.open(dist_path)
    im = preprocess(im)
    
    # Perform inference using the ResNet-34 model
    with torch.no_grad():
        outputs = model(im.unsqueeze(0))
    
    # Get the predicted class index
    predicted_class_index = torch.argmax(outputs).item()
   
    # Get the predicted class label
    predicted_class = class_labels[predicted_class_index]
   
    # Create an ImageSendMessage
    """image_url = request.url_root + '/' + dist_path
    image_message = ImageSendMessage(
        original_content_url=image_url,
        preview_image_url=image_url,
        alt_text=predicted_class
    )"""
    
    # Respond with the predicted class label and the image
    response_text = f"The predicted class is: {predicted_class}"
    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(text=response_text)
            
        ]
    )

@app.route('/static/<path:path>')
def send_static_content(path):
    return send_from_directory('static', path)

# create tmp dir for download content
make_static_tmp_dir()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)


    
    
