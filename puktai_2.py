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
    MessageEvent, ImageMessage, TextSendMessage, ImageSendMessage,TextMessage
)
from linebot.models import QuickReply, QuickReplyButton, MessageAction
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

@handler.add(MessageEvent, message=(TextMessage))
def handle_text_message(event):
    if event.message.text == "ขอเมนู":
        image_path = "https://i.imgur.com/HRV9vrY.jpg"
        line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
    else:
        pass
# Preprocess function for image classification
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# คลาสของอาหาร
class_labels = {
 0:"ไก่ต้มขมิ้น",
 1:"เเกงคั่วหอยขมใบชะพลู",
 2:"ขนมจีนนํ้ายาปู",
 3:"ไก่กอเเละ",
 4:"ไก่ทอดหาดใหญ่",
 5:"ไข่ครอบ",
 6:"ข้าวยํา",
 7:"คั่วกลิ้งหมู",
 8:"ใบเหลียงต้มกะทิกุ้งสด",
 9:"หมูฮ้อง",
 10:"นํ้าพริกกะปิ",
 11:"นํ้าพริกกุ้งเสียบ",
 12:"ปลากรายทอดขมิ้น",
 13:"เเกงเหลืองปลากระพง",
 14:"ใบเหลียงผัดไข่",
 15:"หมูผัดกะปิ",
 16:"สะตอผัดกุ้ง",
 17:"เเกงไตปลา",
}


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



# image processing

    im = Image.open(dist_path)
    im = preprocess(im)        
    with torch.no_grad():
        outputs = model(im.unsqueeze(0))   
   
        _, predict = torch.max(outputs, 1)
        pred_id = predict.item()      
    predicted_class = class_labels[pred_id]
    response_text = f"ชนิดของอาหาร : {predicted_class}"
    
    
    
    # ไก่ต้มขมิ้น
    if pred_id == 0:    
        image_path0 = "https://i.imgur.com/98paZEJ.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path0, preview_image_url=image_path0)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วัตถุดิบที่ใช้":
                img1 = "https://i.imgur.com/s5yd60s.jpg"
                txt1 = "1.น่องไก่ติดสะโพกสับ 1 กิโลกรัม 2.เกลือ 1 ช้อนโต๊ะ 3.น้ำซุป 5 ลิตร 4.รากผักชี 2 ราก 5.น้ำปลา 1 ช้อนโต๊ะ  6.ขมิ้นชันสด 2 แง่ง  7.กระเทียมปอก 5 กลีบ  8.หอมแดงปอก 10 ลูก 9.ตะไคร้บุบ 2 ต้น  10.ใบมะกรูด 2 ใบ 11.ข่าบุบ ½ แง่ง 12.ผักชี "
                line_bot_api.reply_message(event.reply_token, [
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),TextSendMessage(text=txt1)])
    
        
            elif event.message.text == "วิธีการปรุง":
                
                img1 = "https://i.imgur.com/spihkQ4.jpg"
                img2 = "https://i.imgur.com/FYWqxFQ.jpg"
                head1 = " STEP 1 : ต้มสมุนไพร "          
                txt1 = f"บุบสมุนไพรให้แหลก"
                txt2 = f"ต้มสมุนไพรให้มีกลิ่นหอม"
                
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img2, preview_image_url=img2),                    
                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":
                    head1 = " STEP 2 :  ใส่เนื้อไก่ "
                    img1 = "https://i.imgur.com/czE5AyS.jpg"
                    img2 = "https://i.imgur.com/MdWbKdH.jpg"
                    txt1 = f"ใส่เนื้อไก่ลงไป"
                    txt2 = f"ปรุงรสด้วยเกลือเเละนํ้าปลา"
                    line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img2, preview_image_url=img2),                    
                    ])
                else:
                    pass
                @handler.add(MessageEvent, message=(TextMessage))
                def handle_text_message(event):
                    if event.message.text == "ขั้นต่อไป":
                        head1 = " STEP 3: จัดเสิร์ฟ "
                        img1 = "https://i.imgur.com/kOGz8yl.jpg"
                        img2 = "https://i.imgur.com/imTFsVi.jpg"
                        txt1 = f"คอยช้อนฟองออกเพื่อให้นํ้าใส"
                        txt2 = f"ไก่นุ่มนํ้าเเกงหรอย ซดคล่องคอ!"
                        line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=head1),
                        TextSendMessage(text=txt1),
                        ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                        TextSendMessage(text=txt2),
                        ImageSendMessage(original_content_url=img2, preview_image_url=img2),                    
                        ])
                    else:
                        pass     


    # เเกงคั่วหอยขม
    if pred_id == 1 :    
        image_path1 = "https://i.imgur.com/L2OKS5r.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path1, preview_image_url=image_path1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วัตถุดิบที่ใช้":
                img1 = "https://i.imgur.com/nIjfdFR.jpg"
                txt1 = "1.หอยขม 500 กรัม 2.ใบชะพลู 50 กรัม 3.ใบชะอม 50 กรัม 4.ใบมะกรูดฉีก 1 ช้อนโต๊ะ 5.กะทิ 1 ½ ถ้วย 6.น้ำปลา 2 ช้อนโต๊ะ 7.น้ำตาลปี๊บ 1 ช้อนโต๊ะ 8.พริกแกง 2 ช้อนโต๊ะ 9.แครอท 2 ช้อนโต๊ะ 10.น้ำมันพืช 1 ช้อนโต๊ะ"
                line_bot_api.reply_message(event.reply_token, [
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),TextSendMessage(text=txt1)])
    
            elif event.message.text == "วิธีการปรุง":
                
                img1 = "https://i.imgur.com/zYqXOq5.jpg"
                img2 = "https://i.imgur.com/Y7aMSXB.jpg"
                head1 = " STEP 1 : ตั้งกระทะผัดพริกเเกง "          
                txt1 = f"นําพริกเเกงลงไปผัด"
                txt2 = f"เติมหางกะทิลงไป"
                
                
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img2, preview_image_url=img2),                    
                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":
                    head1 = " STEP 2 :  ใส่ส่วนผสม + ปรุงรส "
                    img1 = "https://i.imgur.com/EsYnZ5y.jpg"
                    img2 = "https://i.imgur.com/iWtHNQT.jpg"
                    txt1 = f"ใส่ใบชะพลูลงไป"
                    txt2 = f"ใส่ชะอมลงไป"
                    line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img2, preview_image_url=img2),                    
                    ])
                else:
                    pass
                @handler.add(MessageEvent, message=(TextMessage))
                def handle_text_message(event):
                    if event.message.text == "ขั้นต่อไป":
                        
                        img1 = "https://i.imgur.com/4a6ZFQ0.jpg"
                        img2 = "https://i.imgur.com/jBhUb0v.jpg"
                        txt1 = f"ใส่เเครอทลงไป"
                        txt2 = f"ปรุงรสด้วยนํ้าปลา"
                        line_bot_api.reply_message(event.reply_token, [
                        ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                        TextSendMessage(text=txt1),
                        ImageSendMessage(original_content_url=img2, preview_image_url=img2), 
                        TextSendMessage(text=txt2),                   
                        ])
                    else:
                        pass  
                    @handler.add(MessageEvent, message=(TextMessage))
                    def handle_text_message(event):
                        if event.message.text == "ขั้นต่อไป":  
                            img1 = "https://i.imgur.com/z1WzALa.jpg"
                            head1 = f" STEP  3: จัดเสิร์ฟ "
                            txt1 = f" ตักเเกงคั่วหอยขมขึ้นมาใส่ชาม โรยด้วยใบมะกรูดหั่นฝอย ตกเเต่งให้สวยงาม เเล้วก็จัดเสิร์ฟได้เลยครับ "
                            txt2 = f"เมนู เเกงคั่วหอยขม พร้อมเสิร์ฟเเล้วครับ!"
                            line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=head1),   
                        TextSendMessage(text=txt1),     
                        ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                        TextSendMessage(text=txt2),                   
                        ])
                        else:
                            pass 

    # ขนมจีนนํ้ายากะทิ    
    if pred_id == 2 :    
        image_path2 = "https://i.imgur.com/m1ISgOM.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path2, preview_image_url=image_path2)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วัตถุดิบที่ใช้":
                img1 = "https://i.imgur.com/Vyhk3MH.png"
                txt1 = "1.ตะไคร้ 200 กรัม 2.กระเทียม 30 กรัม 3.หอมแดง 50 กรัม 4.ข่า 60 กรัม 5.กระชาย 400 กรัม 6.พริกแห้ง 20 เม็ด 7.เนื้อปลาตาเดียว 500 กรัม 8.กะทิ 250 มิลลิลิตร 9.น้ำเปล่า 4 ถ้วย 10.น้ำปลา 3 ช้อนโต๊ะ 11.เกลือ 2 ช้อนชา 12.ลูกชิ้นปลา 150 กรัม 13.ผักกินแกล้ม (ถั่วงอก, โหระพา, ถั่วฝักยาว, ผักกาดดอง)"
                line_bot_api.reply_message(event.reply_token, [
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),TextSendMessage(text=txt1)])
            
            elif event.message.text == "วิธีการปรุง":
                
                head1 = f"STEP 1 : เตรียมเครื่องแกงน้ำยากะทิ"
                img1 = "https://i.imgur.com/OnG3We3.png"
                txt1 = f"ใส่ตะไคร้ กระเทียม หอมเเดง ข่า กระชาย เเละพริกเเห้งลงไป เเละตามด้วยเนื้อปลา ต้มจนสุก"
                img2 = "https://i.imgur.com/ZU5pbqW.png"
                txt2 = f"นําผัก เเละเนื้อปลาที่ต้มมาโขลกให้ละเอียด"
                
                
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img2, preview_image_url=img2),                    
                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":
                    head1 = " STEP 2 : ทํานํ้ายากะทิ "
                    img1 = "https://i.imgur.com/qQD2bM5.png"
                    img2 = "https://i.imgur.com/Sc9Deq9.png"
                    txt1 = f"นำเครื่องแกงลงไปผัดกับกะทิจนเข้ากัน"
                    txt2 = f"เติมกะทิส่วนที่เหลือลงไปในเครื่องแกงที่ผัดไว้ก่อนหน้านี้"
                    line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img2, preview_image_url=img2),                    
                    ])
                else:
                    pass
                @handler.add(MessageEvent, message=(TextMessage))
                def handle_text_message(event):
                    if event.message.text == "ขั้นต่อไป":
                        head1 = f"STEP  3: จัดเสิร์ฟ"
                        img1 = "https://i.imgur.com/9mB7lXo.png"
                        img2 = "https://i.imgur.com/VwJ8Ih6.png"
                        txt1 = f"ตักน้ำยากะทิใส่จานเตรียมเสิร์ฟ"
                        txt2 = f"ขนมจีนนํ้ายากะทิ พร้อมรับประทานเเล้วครับ"
                        line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=head1), 
                        TextSendMessage(text=txt1),   
                        ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                        TextSendMessage(text=txt2), 
                        ImageSendMessage(original_content_url=img2, preview_image_url=img2),                 
                        ])
                    else:
                        pass  
                    
                    
    ## ไก่กอเเละ        
    if pred_id == 3 :    
        image_path3 = "https://i.imgur.com/o4Ib06J.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path3, preview_image_url=image_path1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                image_path = ""
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
            else:
                pass    

    ## ไก่ทอด    
    if pred_id == 4 :    
        image_path4 = "https://i.imgur.com/u5NbV4t.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path4, preview_image_url=image_path0)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                image_path = ""
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
            else:
                pass

    ## ไข่ครอบ       
    if pred_id == 5 :    
        image_path5 = "https://i.imgur.com/Wpbm0om.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path5, preview_image_url=image_path1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                image_path = ""
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
            else:
                pass    
    ## ข้าวยํา   
    if pred_id == 6 :    
        image_path6 = "https://i.imgur.com/NjNhU1f.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path6, preview_image_url=image_path0)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                image_path = ""
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
            else:
                pass

    ##  คั่วกลิ้งหมู                         
    if pred_id == 7 :    
        image_path7 = "https://i.imgur.com/dRbRWYy.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path7, preview_image_url=image_path0)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                image_path = ""
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
            else:
                pass

    ##  ใบเหลียงต้มกะทิกุ้งสด      
    if pred_id == 8 :    
        image_path8 = "https://i.imgur.com/77Mentt.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path8, preview_image_url=image_path1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                image_path = ""
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
            else:
                pass
            
    ##  หมูฮ้อง  
    if pred_id == 9 :    
        image_path9 = "https://i.imgur.com/RD14EaT.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path9, preview_image_url=image_path0)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                image_path = ""
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
            else:
                pass

    ##  นํ้าพริกกะปิ      
    if pred_id == 10 :    
        image_path10 = "https://i.imgur.com/NjNhU1f.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path10, preview_image_url=image_path10)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                image_path = ""
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
            else:
                pass    


    ##  นํ้าพริกกุ้งเสียบ  
    if pred_id == 11 :    
        image_path11 = "https://i.imgur.com/77Mentt.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path11, preview_image_url=image_path0)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                image_path = ""
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
            else:
                pass

    ##  ปลากรายทอดขมิ้น      
    if pred_id == 12 :    
        image_path12 = "https://i.imgur.com/rOwd3kW.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path12, preview_image_url=image_path0)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                image_path = ""
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
            else:
                pass

    ##  เเกงเหลืองปลากระพง
    if pred_id == 13 :    
        image_path13 = "https://i.imgur.com/uTNu4sF.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path13, preview_image_url=image_path1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                image_path = ""
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
            else:
                pass

    ##  ใบเหลียงผัดไข่   
    if pred_id == 14 :    
        image_path14 = "https://i.imgur.com/5KzhmaC.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path14, preview_image_url=image_path0)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                image_path = ""
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
            else:
                pass

    ##  หมูผัดกะปิ      
    if pred_id == 15 :    
        image_path15 = "https://i.imgur.com/WAAuoW2.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path15, preview_image_url=image_path1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                image_path = ""
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
            else:
                pass  

          
    ##  สะตอผัดกุ้ง  
    if pred_id == 16 :    
        image_path16= "https://i.imgur.com/P8STLYP.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path16, preview_image_url=image_path0)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                image_path = ""
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
            else:
                pass 

    ##  เเกงไตปลา              
    if pred_id == 17 :    
        image_path17 = "https://i.imgur.com/oZj6CMy.jpg"            
        line_bot_api.reply_message(event.reply_token, [TextSendMessage(text=response_text),ImageSendMessage(original_content_url=image_path17, preview_image_url=image_path0)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                image_path = ""
                line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
            else:
                pass
       
             

@handler.add(MessageEvent, message=(TextMessage))
def handle_text_message(event):
    if event.message.text == "ขอเมนู":
        image_path = "https://i.imgur.com/HRV9vrY.jpg"
        line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=image_path, preview_image_url=image_path))
    else:
        pass
@app.route('/static/<path:path>')
def send_static_content(path):
    return send_from_directory('static', path)

# create tmp dir for download content
make_static_tmp_dir()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

    
    
