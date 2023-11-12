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
          
        img1 = "https://i.imgur.com/98paZEJ.jpg"
        txt = f"ไก่ต้มขมิ้น : แก้ไอ ขับเสมหะ เพิ่มความสดชื่นให้กับร่างกาย"            
        line_bot_api.reply_message(event.reply_token, [
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt),
                                            
                    ])
                
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                
                img1 = "https://i.imgur.com/spihkQ4.jpg"
                img2 = "https://i.imgur.com/FYWqxFQ.jpg"
                head1 = " STEP 1/3 : ต้มสมุนไพร "          
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
                    head1 = " STEP 2/3 :  ใส่เนื้อไก่ "
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
                        head1 = " STEP 3/3: จัดเสิร์ฟ "
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
                    @handler.add(MessageEvent, message=(TextMessage))
                    def handle_text_message(event): 
                        if event.message.text == "ขั้นต่อไป":
                            txt = "ไม่มีขั้นตอนต่อไปเเล้วครับ" 
                            line_bot_api.reply_message(event.reply_token, [
                            TextSendMessage(text=txt)])  


    # เเกงคั่วหอยขม
    if pred_id == 1 :    
        image_path1 = "https://i.imgur.com/L2OKS5r.jpg"
        txt1 = f"แกงคั่วหอยขมใบชะพลู : เปลือกและเนื้อหอยมีสรรพคุณช่วยแก้กระษัยต่างๆ เช่น แก้ปวดเมื่อย บำรุงกำลัง บำรุงถุงน้ำดี และโรคทางเดินปัสสาวะอย่างโรคนิ่ว" 
        txt2 = f"ปริมาณโซเดียมสูง (>600 mg ซึ่งเป็นปริมาณโซเดียมปกติใน 1 จาน)"          
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path1, preview_image_url=image_path1),TextSendMessage(text=txt1),TextSendMessage(text=txt2)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            
            if event.message.text == "วิธีการปรุง":
                
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
                        @handler.add(MessageEvent, message=(TextMessage))
                        def handle_text_message(event): 
                            if event.message.text == "ขั้นต่อไป":
                                txt = "ไม่มีขั้นตอนต่อไปเเล้วครับ" 
                                line_bot_api.reply_message(event.reply_token, [
                                TextSendMessage(text=txt)])

    # ขนมจีนนํ้ายากะทิ    
    if pred_id == 2 :    
        image_path2 = "https://i.imgur.com/m1ISgOM.jpg"
        txt1 = f"ขนมจีนน้ำยาปู : ช่วยป้องกันท้องผูก"
        txt2 = f"ปริมาณโซเดียมสูงมาก  ผู้ป่วยโรคที่เกี่ยวกับความเค็ม ไม่ควรรับประทาน(>>>600 mg ซึ่งเป็นปริมาณโซเดียมปกติใน 1 จาน)"            
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path2, preview_image_url=image_path2),TextSendMessage(text=txt1),TextSendMessage(text=txt2)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            
            if event.message.text == "วิธีการปรุง":
                
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
                    ImageSendMessage(original_content_url=img2, preview_image_url=img2)                    
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
                    ImageSendMessage(original_content_url=img2, preview_image_url=img2)                   
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
                        ImageSendMessage(original_content_url=img2, preview_image_url=img2)                 
                        ])
                    else:
                        pass
                    @handler.add(MessageEvent, message=(TextMessage))
                    def handle_text_message(event): 
                        if event.message.text == "ขั้นต่อไป":
                            txt = "ไม่มีขั้นตอนต่อไปเเล้วครับ" 
                            line_bot_api.reply_message(event.reply_token, [
                                TextSendMessage(text=txt)])  
                    
                    
    ## ไก่กอเเละ        
    if pred_id == 3 :    
        image_path3 = "https://i.imgur.com/o4Ib06J.jpg"
        txt1 = f"ไก่กอและ : เป็นอาหารประจำถิ่น “ของดีเมืองเบตง”"
        txt2 = f"ปริมาณโซเดียมสูงมาก  ผู้ป่วยโรคที่เกี่ยวกับความเค็ม ไม่ควรรับประทาน(>>>600 mg ซึ่งเป็นปริมาณโซเดียมปกติใน 1 จาน)"            
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path3, preview_image_url=image_path3),TextSendMessage(text=txt1),TextSendMessage(text=txt2)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                
                head1 = f" STEP 1/3 : ทําพริกเเกง "
                img1 = "https://i.imgur.com/HwweMbL.png"
                txt1 = f"โขลกพริกแกงให้ละเอียด"
                img2 = "https://i.imgur.com/NFbdD60.jpg"
                txt2 = f"ใส่กะทิลงไปเคี่ยวจนแตกมัน"
                
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img2, preview_image_url=img2)                    
                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":
                    head1 = " STEP 2/3 : หมักไก่ "
                    img1 = "https://i.imgur.com/Ukfn9b3.png"
                    img2 = "https://i.imgur.com/zN28TlL.jpg"
                    txt1 = f"โขลกกระเทียม ผงขมิ้น และเกลือป่น ให้ละเอียด"
                    txt2 = f"หมักไก่ไว้ 30 นาที"
                    line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img2, preview_image_url=img2)                    
                    ])
                else:
                    pass
                @handler.add(MessageEvent, message=(TextMessage))
                def handle_text_message(event):
                    if event.message.text == "ขั้นต่อไป":
                        head1 = f" STEP  3/3 : ย่าง "
                        img1 = "https://i.imgur.com/nTDTJnb.png"
                        img2 = "https://i.imgur.com/fAQpNj3.png"
                        txt1 = f"นำไก่ที่หมักไว้มาเสียบไม้"
                        txt2 = f"ทาด้วยพริกแกงที่ทำไว้อย่างสม่ำเสมอทั้งสองด้าน"
                        line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=head1), 
                        TextSendMessage(text=txt1),   
                        ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                        TextSendMessage(text=txt2), 
                        ImageSendMessage(original_content_url=img2, preview_image_url=img2)                 
                        ])
                    else:
                        pass
                    @handler.add(MessageEvent, message=(TextMessage))
                    def handle_text_message(event): 
                        if event.message.text == "ขั้นต่อไป":
                            txt = "ไม่มีขั้นต่อไปเเล้วครับ" 
                            line_bot_api.reply_message(event.reply_token, [
                                TextSendMessage(text=txt)])    
                

    ## ไก่ทอด    
    if pred_id == 4 :    
        image_path4 = "https://i.imgur.com/u5NbV4t.jpg"   
        txt1 = f"ไก่ทอดหาดใหญ่ : เป็นอาหารประจำถิ่น “ของเมืองหาดใหญ่”"
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path4, preview_image_url=image_path4),TextSendMessage(text=txt1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                
                txt1 = "1.ล้างไก่ให้สะอาด พักในตะแกรงให้สะเด็ดน้ำ"
                txt2 = "2.โขลก พริกไทย, ลูกผักชี, และยี่หร่า เข้าด้วยกันให้ละเอียด"
                txt3 = "3.เสร็จแล้วค่อยใส่กระเทียม,เกลือป่น และน้ำตาลทรายแดง โขลกทุกอย่างให้ละเอียดอีกครั้ง"
                txt4 = "4.จากนั้นนำทุกอย่างไปผสมกับไก่ และ ซีอิ๊วขาวหรือซอสปรุงรส คลุกส่วนผสม ทั้งหมดให้เข้ากัน หมักทิ้งในตู้เย็น อย่างน้อย 3 ชั่วโมง"
                
                
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=txt1),
                    TextSendMessage(text=txt2),
                    TextSendMessage(text=txt3),
                    TextSendMessage(text=txt4)                  
                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":       
                    txt1 = "5.เมื่อหมักไก่จนได้ที่แล้ว ให้นำไปคลุกกับแป้งสาลีและ แป้งข้าวเจ้า"
                    txt2 = "6.นำไก่ทอดในน้ำมันพืชที่ร้อนได้ที่ด้วยไฟปานกลาง จนสุกเป็นสีน้ำตาลทอง (ใช้เวลาประมาณ 10-12 นาที) ตักขึ้น พักในบนกระดาษซับมันประมาณ 3-4 นาที"
                    txt3 = "7.เสิร์ฟคู่กับหอมเจียว และ น้ำจิ้มไก่ตราแม่ประนอมก็ดีงามใช่ย่อย"           
                    line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=txt1),
                        TextSendMessage(text=txt2),
                        TextSendMessage(text=txt3),
                                            
                    ])
                else:
                    pass
                
                @handler.add(MessageEvent, message=(TextMessage))
                def handle_text_message(event): 
                    if event.message.text == "ขั้นต่อไป":
                        txt = "ไม่มีขั้นต่อไปเเล้วครับ" 
                        line_bot_api.reply_message(event.reply_token, [
                            TextSendMessage(text=txt)])

    ## ไข่ครอบ       
    if pred_id == 5 :    
        image_path5 = "https://i.imgur.com/Wpbm0om.jpg" 
        txt1 = f"ไข่ครอบ : เป็นอาหารประถิ่น “ของชาวประมงพื้นบ้านรอบริมทะเลสาบสงขลา” มีสารต้านอนุมูลอิสระที่ช่วยป้องกันโรคต่างๆ เช่น โรคหัวใจ โรคประสาท ไปจนถึงภาวะสมองเสื่อมหรืออัลไซเมอร์"           
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path5, preview_image_url=image_path5),TextSendMessage(text = txt1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                
                head1 = f" STEP 1 : เเยกไข่ "
                img1 = "https://i.imgur.com/2zgRulv.jpg"
                txt1 = f"เลาะเปลือกไข่ข้างบนออก ใส่ไข่ลงไปในภาชนะ"
                img2 = "https://i.imgur.com/qeCp5OZ.jpg"
                txt2 = f"ใส่เกลือลงไปในน้ำ"
                
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img2, preview_image_url=img2)                    
                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":
                    head1 = " STEP 1.5/3 : เเยกไข่ "
                    img1 = "https://i.imgur.com/dvkFhsl.jpg"
                    img2 = "https://i.imgur.com/UKbAvBy.jpg"
                    txt1 = f"แยกไข่แดงออกจากไข่ขาว นำไปแช่น้ำเกลือ"
                    txt2 = f"แช่น้ำเกลือ 5 ชั่วโมง"
                    line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img2, preview_image_url=img2)                    
                    ])
                else:
                    pass
                @handler.add(MessageEvent, message=(TextMessage))
                def handle_text_message(event):
                    if event.message.text == "ขั้นต่อไป":
                        head1 = f" STEP 2/3 : ตัดแต่งเปลือกและหยอดไข่ "
                        img1 = "https://i.imgur.com/uwL3GwM.jpg"
                        img2 = "https://i.imgur.com/TIYQQTh.jpg"
                        txt1 = f"ตัดแต่งเปลือกไข่"
                        txt2 = f"ตัดแต่งเปลือกไข่"
                        line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=head1), 
                        TextSendMessage(text=txt1),   
                        ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                        TextSendMessage(text=txt2), 
                        ImageSendMessage(original_content_url=img2, preview_image_url=img2)                 
                        ])
                    else:
                        pass
                    @handler.add(MessageEvent, message=(TextMessage))
                    def handle_text_message(event):
                        if event.message.text == "ขั้นต่อไป":
                            head1 = f" STEP 2.5/3 : ตัดแต่งเปลือกและหยอดไข่ "
                            img1 = "https://i.imgur.com/er2FQul.jpg"
                            img2 = "https://i.imgur.com/hvw1HlV.png"
                            txt1 = f"นำไข่แดงใส่ในเปลือกไข่ที่เราตัดไว้"
                            txt2 = f"ใส่เรียบร้อย"
                            line_bot_api.reply_message(event.reply_token, [
                            TextSendMessage(text=head1), 
                            TextSendMessage(text=txt1),   
                            ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                            TextSendMessage(text=txt2), 
                            ImageSendMessage(original_content_url=img2, preview_image_url=img2)                 
                            ])
                        else:
                            pass
                        @handler.add(MessageEvent, message=(TextMessage))
                        def handle_text_message(event):
                            if event.message.text == "ขั้นต่อไป":
                                head1 = f"STEP  3/3: นําไปนึ่ง "
                                img1 = "https://i.imgur.com/Lw6zf2O.jpg"
                                img2 = "https://i.imgur.com/fqa3KPz.jpg"
                                txt1 = f"หยอดน้ำเกลือ"
                                txt2 = f"นําไปนึ่ง"
                                line_bot_api.reply_message(event.reply_token, [
                                TextSendMessage(text=head1), 
                                TextSendMessage(text=txt1),   
                                ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                                TextSendMessage(text=txt2), 
                                ImageSendMessage(original_content_url=img2, preview_image_url=img2)                 
                                ])
                            else:
                                pass
                            @handler.add(MessageEvent, message=(TextMessage))
                            def handle_text_message(event):
                                if event.message.text == "ขั้นต่อไป":
                                    img1 = "https://i.imgur.com/1LrS6D0.jpg"
                                    img2 = "[img]https://i.imgur.com/MLdz6W3.jpg[/img]"
                                    txt1 = f"ใช้เวลานึ่ง 3-5 นาที"
                                    txt2 = f"สุกแล้ว"
                                    txt3 = f"พร้อมเสิร์ฟ"
                                    line_bot_api.reply_message(event.reply_token, [
                                    
                                    TextSendMessage(text=txt1),   
                                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                                    TextSendMessage(text=txt2), 
                                    ImageSendMessage(original_content_url=img2, preview_image_url=img2),
                                    TextSendMessage(text=txt3)               
                                    ])
                                else:
                                    pass
                        
                                @handler.add(MessageEvent, message=(TextMessage))
                                def handle_text_message(event): 
                                    if event.message.text == "ขั้นต่อไป":
                                        txt = "ไม่มีขั้นต่อไปเเล้วครับ" 
                                        line_bot_api.reply_message(event.reply_token, [
                                            TextSendMessage(text=txt)])    
    ## ข้าวยํา   
    if pred_id == 6 :    
        image_path6 = "https://i.imgur.com/NjNhU1f.jpg"  
        txt1 = f"ข้าวยำ : เหมาะสมกับคนที่ต้องการลดน้ำหนัก หรือควบคุมน้ำหนัก ทั้งยังช่วยให้ระบบขับถ่ายดี"          
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path6, preview_image_url=image_path6),TextSendMessage(text=txt1)])
        
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                
                head1 = f" STEP 1/3 : หุงข้าวให้เป็นสีฟ้า "
                img1 = "https://i.imgur.com/HioDlhI.png"
                txt1 = f"ใส่ดอกอัญชัน"
                img2 = "https://i.imgur.com/awZo1aG.png"
                txt2 = f"หุงให้สุก"
                
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img2, preview_image_url=img2)                    
                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":
                    head1 = " STEP 2/3 : หมักไก่ "
                    img1 = "https://i.imgur.com/Ukfn9b3.png"
                    img2 = "https://i.imgur.com/zN28TlL.jpg"
                    txt1 = f"โขลกกระเทียม ผงขมิ้น และเกลือป่น ให้ละเอียด"
                    txt2 = f"หมักไก่ไว้ 30 นาที"
                    line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img2, preview_image_url=img2)                    
                    ])
                else:
                    pass
                @handler.add(MessageEvent, message=(TextMessage))
                def handle_text_message(event):
                    if event.message.text == "ขั้นต่อไป":
                        head1 = f" STEP  3/3 : ย่าง "
                        img1 = "https://i.imgur.com/nTDTJnb.png"
                        img2 = "https://i.imgur.com/fAQpNj3.png"
                        txt1 = f"นำไก่ที่หมักไว้มาเสียบไม้"
                        txt2 = f"ทาด้วยพริกแกงที่ทำไว้อย่างสม่ำเสมอทั้งสองด้าน"
                        line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=head1), 
                        TextSendMessage(text=txt1),   
                        ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                        TextSendMessage(text=txt2), 
                        ImageSendMessage(original_content_url=img2, preview_image_url=img2)                 
                        ])
                    else:
                        pass
                    @handler.add(MessageEvent, message=(TextMessage))
                    def handle_text_message(event): 
                        if event.message.text == "ขั้นต่อไป":
                            txt = "ไม่มีขั้นต่อไปเเล้วครับ" 
                            line_bot_api.reply_message(event.reply_token, [
                                TextSendMessage(text=txt)])

    ##  คั่วกลิ้งหมู                         
    if pred_id == 7 :    
        image_path7 = "https://i.imgur.com/dRbRWYy.jpg"  
        txt1 = f"คั่วกลิ้งหมู : มีสารต้านอนุมูลอิสระ ป้องกันการเกิดมะเร็งในตับ ช่วยบำรุงตับ"          
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path7, preview_image_url=image_path7),TextSendMessage(text=txt1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                
                head1 = f" STEP 1/3 : ผัดพริกเเกง "
                img1 = "https://i.imgur.com/T0DWJtS.png"
                txt1 = f"ใส่พริกเเกงลงไปเเล้วผัดให้หอม"
                
                txt2 = f"ตั้งกระทะโดยใช้ไฟกลาง พอกระทะร้อนใส่น้ำมันลงไปตามด้วยพริกแกงคั่วกลิ้ง ผัดให้มีกลิ่นหอม"
                
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt1)
                                        
                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":
                    head1 = " STEP 2/3 : ใส่หมูสับ + ปรุงรส "
                    img1 = "https://i.imgur.com/brprJ7k.png"
                    img2 = "https://i.imgur.com/RjGPTCE.png"
                    txt1 = f"ใส่เนื้อหมูลงไป"
                    txt2 = f"ปรุงรสด้วยเกลือเเละนํ้าปลา"
                    line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img2, preview_image_url=img2)                    
                    ])
                else:
                    pass
                @handler.add(MessageEvent, message=(TextMessage))
                def handle_text_message(event):
                    if event.message.text == "ขั้นต่อไป":
                        head1 = f" STEP  2/3 : ใส่หมูสับ + ปรุงรส "
                        img1 = "https://i.imgur.com/nTDTJnb.png"
                        img2 = "https://i.imgur.com/fAQpNj3.png"
                        txt1 = f"ปรุงรส"
                        txt2 = f"เพิ่มความหอมด้วยใบมะกรูด"
                        line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=head1), 
                        TextSendMessage(text=txt1),   
                        ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                        TextSendMessage(text=txt2), 
                        ImageSendMessage(original_content_url=img2, preview_image_url=img2)                 
                        ])
                    else:
                        pass
                    @handler.add(MessageEvent, message=(TextMessage))
                    def handle_text_message(event):
                        if event.message.text == "ขั้นต่อไป":
                            head1 = f" STEP  2/3 : ใส่หมูสับ + ปรุงรส "
                            img1 = "https://i.imgur.com/nTDTJnb.png"
                            img2 = "https://i.imgur.com/fAQpNj3.png"
                            txt1 = f"เพิ่มสีสันด้วยพริกชี้ฟ้าเเดง"
                            txt2 = f"ผัดให้เข้ากัน เเค่นี้ก็พร้อมทานเเล้ว"
                            line_bot_api.reply_message(event.reply_token, [
                            TextSendMessage(text=head1), 
                            TextSendMessage(text=txt1),   
                            ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                            TextSendMessage(text=txt2), 
                            ImageSendMessage(original_content_url=img2, preview_image_url=img2)                 
                            ])
                        else:
                            pass
                        @handler.add(MessageEvent, message=(TextMessage))
                        def handle_text_message(event):
                            if event.message.text == "ขั้นต่อไป":
                                head1 = f" STEP  3/3 : จัดเสิร์ฟ "
                                img1 = "https://i.imgur.com/nTDTJnb.png"
                                
                                txt1 = f"นำคั่วกลิ้งหมูที่สุกแล้วจัดเสิร์ฟใส่จาน ตกแต่งด้วยใบโหระพา พริกชี้ฟ้าแดงซอย และใบมะกรูดซอย กินกับผักเครื่องเคียงตามชอบได้เลยครับ"
                                
                                line_bot_api.reply_message(event.reply_token, [
                                TextSendMessage(text=head1), 
                                TextSendMessage(text=txt1),   
                                ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                                ])
                            else:
                                pass
                            @handler.add(MessageEvent, message=(TextMessage))
                            def handle_text_message(event): 
                                if event.message.text == "ขั้นต่อไป":
                                    txt = "ไม่มีขั้นต่อไปเเล้วครับ" 
                                    line_bot_api.reply_message(event.reply_token, [
                                        TextSendMessage(text=txt)])

    ##  ใบเหลียงต้มกะทิกุ้งสด      
    if pred_id == 8 :    
        image_path8 = "https://i.imgur.com/77Mentt.jpg" 
        txt1 = f"ใบเหลียงต้มกะทิกุ้งสด : บำรุงกระดูก บำรุงสมอง บำรุงสายตาป้องกันมะเร็ง"           
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path8, preview_image_url=image_path8),TextSendMessage(text=txt1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                
                head1 = f" STEP 1/3 : เตรียมเครื่องเเกง "
                txt1 = f"นำใบเหลียงที่เตรียมไว้ล้างน้ำให้สะอาด สะบัดให้สะเด็ดน้ำ เลือกเอาใบอ่อน ๆ ไม่แก่ จะใช้มีดหรือกรรไรตัดให้เล็กลงก็ได้"
                txt2 = f"นำกุ้งสดล้างน้ำให้สะอาด จากนั้นปอกเปลือกออก แล้วผ่าหลังดึงเส้นดำออก ล้างน้ำอีกครั้งพักไว้"
                
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    TextSendMessage(text=txt2)
                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":
                    head1 = " STEP 2/3 : โขลกส่วนผสม "
                    img1 = "https://i.imgur.com/EAKUyOD.png"
                    txt1 = f"นำหอมแดง กะปิ และพริกไทยขาวมาโขลกให้ละเอียด"
                    txt2 = f"ทำการโขลก หอมแดง กะปิ และพริกไทยขาว"
                    line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                                       
                    ])
                else:
                    pass
                @handler.add(MessageEvent, message=(TextMessage))
                def handle_text_message(event):
                    if event.message.text == "ขั้นต่อไป":
                        head1 = f" STEP  3/3 : ลงมือเเกง "
                        img1 = "https://i.imgur.com/gBtdlob.png"
                        img2 = "https://i.imgur.com/5HulU8x.png"
                        txt1 = f"ใส่เครื่องเเกงที่โขลกไว้"
                        txt2 = f"ตามด้วยหางกะทิ"
                        
                        line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=head1), 
                        TextSendMessage(text=txt1),   
                        ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                        TextSendMessage(text=txt2), 
                        ImageSendMessage(original_content_url=img2, preview_image_url=img2)                 
                        ])
                    else:
                        pass
                    @handler.add(MessageEvent, message=(TextMessage))
                    def handle_text_message(event):
                        if event.message.text == "ขั้นต่อไป":
                            head1 = f" STEP  3/3 : ลงมือเเกง "
                            img1 = "https://i.imgur.com/bUYsm3C.png"
                            img2 = "https://i.imgur.com/6WKN23b.png"
                            txt1 = f"ใส่ใบเหลียง"
                            txt2 = f"นำใบเหลียงต้มกะทิตักใส่ชาม พร้อมเสิร์ฟได้เลย"
                            line_bot_api.reply_message(event.reply_token, [
                            TextSendMessage(text=head1), 
                            TextSendMessage(text=txt1),   
                            ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                            TextSendMessage(text=txt2), 
                            ImageSendMessage(original_content_url=img2, preview_image_url=img2)                 
                            ])
                        else:
                            pass
                        @handler.add(MessageEvent, message=(TextMessage))
                        def handle_text_message(event): 
                            if event.message.text == "ขั้นต่อไป":
                                txt = "ไม่มีขั้นต่อไปเเล้วครับ" 
                                line_bot_api.reply_message(event.reply_token, [
                                    TextSendMessage(text=txt)])
            
    ##  หมูฮ้อง  
    if pred_id == 9 :    
        image_path9 = "https://i.imgur.com/RD14EaT.jpg"
        txt1 = "หมูฮ้อง : มีความอร่อยมากเพราะเป็นหมูสามชั้น ดังนั้น ผู้ป่วยโรคหัวใจและหลอดเลือด ไม่ควรรับประทานเป็นประจำ"            
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path9, preview_image_url=image_path9),TextSendMessage(text=txt1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                
                head1 = f" STEP 1/3 : คั่วอบเชย โป๊ยกั๊ก พริกไทยดำ-ขาว "
                img1 = "https://i.imgur.com/tKVQ9y8.png"
                txt1 = f"โดยการให้มีกลิ่นหอม แล้วนำมาตำให้ละเอียด ใส่รากผักชี กระเทียม และเกลือนิดหน่อย ลงไปตำให้เข้ากันสำหรับหมักหมูสามชั้น"
                txt2 = f"คั่วอบเชย โป๊ยกั๊ก พริกไทยดำ-ขาว"
                
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2)
                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":
                    head1 = " STEP 2/3 : หมูสามชั้นหั่นชิ้นหนาประมาณ 2นิ้ว "
                    img1 = "https://i.imgur.com/SVNO56L.png"
                    txt1 = f"หมักให้เข้าเนื้อด้วยเครื่องที่ตำไว้ ปรุงรสด้วยซีอิ้วขาว ซีอิ้วดำ น้ำตาลทรายแดง น้ำตาลปิ๊ป และเกลือเล็กน้อย"
                    txt2 = f"หมักหมูให้เข้ากัน"
                    line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                                       
                    ])
                else:
                    pass
                @handler.add(MessageEvent, message=(TextMessage))
                def handle_text_message(event):
                    if event.message.text == "ขั้นต่อไป":
                        head1 = f" STEP  3/3 : ผัดหมูสามชั้นที่หมักไว้ "
                        img1 = "https://i.imgur.com/jxLahAx.png"
                        txt1 = f"ผัดหมูสามชั้นที่หมักไว้ในกระทะให้พอผิวด้านนอกสุกนิดหน่อย.. แล้วเติมน้ำลงไปใส่ซุปหมูก้อนคนอร์เพิ่มความหอมกลมกล่อม..เคี่ยวให้หมูเปื่อยนุ่มดีใช้เวลาประมาณ 1ชม. น้ำจะงวดลงเข้าเนื้อหมูเข้มข้น..หอมหวลชวนกินเป็นอันเสร็จ"
                        txt2 = f"ผัดให้เข้ากัน"
                        
                        line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=head1), 
                        TextSendMessage(text=txt1),   
                        ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                        TextSendMessage(text=txt2), 
                                         
                        ])
                    else:
                        pass
                    @handler.add(MessageEvent, message=(TextMessage))
                    def handle_text_message(event):
                        if event.message.text == "ขั้นต่อไป":
                            img1 = "https://i.imgur.com/rdx7ROx.png"
                            txt1 = f"หมูฮ้อง หอม ๆ รสชาติเค็มนำหวาน หอมกลิ่นเครื่องเทศต่าง ๆ เปื่อยนุ่มกำลังดี"
                            line_bot_api.reply_message(event.reply_token, [
                            ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                            TextSendMessage(text=txt1) 
                            ])
                        else:
                            pass
                        @handler.add(MessageEvent, message=(TextMessage))
                        def handle_text_message(event): 
                            if event.message.text == "ขั้นต่อไป":
                                txt = "ไม่มีขั้นต่อไปเเล้วครับ" 
                                line_bot_api.reply_message(event.reply_token, [
                                    TextSendMessage(text=txt)])

    ##  นํ้าพริกกะปิ      
    if pred_id == 10 :    
        image_path10 = "https://i.imgur.com/NjNhU1f.jpg" 
        txt1 = f"น้ำพริกกะปิ : ช่วยให้กระดูก และฟันแข็งแรง ช่วยป้องกันการติดเชื้อ และลดไขมันในเส้นเลือด"
        txt2 = f"ปริมาณโซเดียมสูงมาก  ผู้ป่วยโรคที่เกี่ยวกับความเค็ม ไม่ควรรับประทาน(>>>600 mg ซึ่งเป็นปริมาณโซเดียมปกติใน 1 จาน)ปริมาณน้ำตาลสูง  ผู้ป่วยโรคเบาหวาน ไม่ควรรับประทาน(>8 g ซึ่งเป็นปริมาณโซเดียมปกติใน 1 จาน)"           
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path10, preview_image_url=image_path10),TextSendMessage(text=txt1),TextSendMessage(text=txt2)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                
                head1 = f" STEP 1/2 : โขลกเครื่องให้ละเอียด "
                img1 = "https://i.imgur.com/A524lfm.png"
                img2 = "https://i.imgur.com/aPwo8KW.png"
                txt1 = f"ใส่พริกขี้หนู พริกแดง กระเทียม น้ำตาลทราย ลงไปตำ"
                txt2 = f"ใส่กะปิตามลงไป ตำให้เข้ากัน"
                
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1)
                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":
                    head1 = "STEP 2/2 : ปรุงรสน้ำพริก "
                    img1 = "https://i.imgur.com/rNSPMSV.png"
                    img2 = "https://i.imgur.com/zHjYGuF.png"
                    txt1 = f"ปรุงรสด้วยน้ำปลาและน้ำมะนาว"
                    txt2 = f"จัดเสิร์ฟได้เลย"
                    line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1)
                    ])
                else:
                    pass
                
                @handler.add(MessageEvent, message=(TextMessage))
                def handle_text_message(event): 
                    if event.message.text == "ขั้นต่อไป":
                        txt = "ไม่มีขั้นต่อไปเเล้วครับ" 
                        line_bot_api.reply_message(event.reply_token, [
                            TextSendMessage(text=txt)])    


    ##  นํ้าพริกกุ้งเสียบ  
    if pred_id == 11 :    
        image_path11 = "https://i.imgur.com/77Mentt.jpg" 
        txt1 = f"น้ำพริกกุ้งเสียบ : ให้วิตามิน และเบต้าแคโรทีนสูง" 
        txt2 = f"ปริมาณน้ำตาลสูง  ผู้ป่วยโรคเบาหวาน ไม่ควรรับประทาน(>8 g ซึ่งเป็นปริมาณโซเดียมปกติใน 1 จาน)"          
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path11, preview_image_url=image_path11),TextSendMessage(text=txt1),TextSendMessage(text=txt2)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                
                head1 = f" STEP 1/3 : ตำ "
                img1 = "https://i.imgur.com/SYwmhfC.png"
                img2 = "https://i.imgur.com/jtE7rQ8.png"
                txt1 = f"ใส่หอมแดง กระเทียม และพริกขี้หนู ลงในครก"
                txt2 = f"ตำให้ละเอียดเข้ากัน"
                
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img2)
                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":
                    head1 = " STEP 2/3 : คลุก "
                    img1 = "https://i.imgur.com/sloK9VV.png"
                    img2 = "https://i.imgur.com/xvzUIN2.png"
                    txt1 = f"คั่วกุ้งเสียบด้วยไฟกลาง"
                    txt2 = f"คลุกให้เข้ากัน"
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
                        head1 = f" STEP  3/3 : จัดเสิร์ฟ "
                        img1 = "https://i.imgur.com/UPORtkp.png"
                        img2 = "https://i.imgur.com/H9mW2w9.png"
                        txt1 = f"ตักขึ้นใส่ชาม"
                        txt2 = f"เสิร์ฟกับผักสดตามชอบ"
                        
                        line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=head1),
                        TextSendMessage(text=txt1),
                        ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                        TextSendMessage(text=txt2),
                        ImageSendMessage(original_content_url=img2, preview_image_url=img2)          
                        ])
                    else:
                        pass
                    
                    @handler.add(MessageEvent, message=(TextMessage))
                    def handle_text_message(event): 
                        if event.message.text == "ขั้นต่อไป":
                            txt = "ไม่มีขั้นต่อไปเเล้วครับ" 
                            line_bot_api.reply_message(event.reply_token, [
                                TextSendMessage(text=txt)])

    ##  ปลากรายทอดขมิ้น      
    if pred_id == 12 :    
        image_path12 = "https://i.imgur.com/rOwd3kW.jpg"
        txt1 = f"ปลากรายทอดขมิ้น : เป็นสารต้านอนุมูลอิสระ ฆ่าเชื้อแบคทีเรีย เชื้อรา ช่วยลดการอักเสบ ป้องกันและรักษาโรคกระเพาะอาหาร ขับลม ลดอาการท้องอืดท้องเฟ้อ"            
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path12, preview_image_url=image_path12),TextSendMessage(text=txt1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "ขั้นต่อไป":
                
                txt1 = f"1. ตำกระเทียมกับขมิ้นให้พอแหลกครับ (ขมิ้นจะมียางหน่อยๆ เวลาตำแล้วจะรู้สึกว่าตำยากนิดๆ ครับ แล้วครกจะเหลืองติดสีไปซักพักเลยครับ)"
                txt2 = f"2.เอาเครื่องทำตำแล้วกับเกลือเคล้ากับตัวปลาให้ทั่ว ทั้งข้างนอก ข้างใน แล้วพักไว้ 15 นาที"
                txt3 = f"3. นำลงทอดในกระทะใส่น้ำมันมากหน่อยตั้งไฟให้ร้อนจัด"
                txt4 = f"4. ใช้มือรูดเครื่องที่หมักออกจากตัวปลาบ้าง (ถ้าใส่ลงไปพร้อมกับเครื่องหมักจะไหม้ก่อนปลาสุกครับ) นำลงทอดจะสุก เหลือง ถ้าชอบกินเครื่องหมักทอดให้นำเครื่องหมักลงลงทอดจนเหลืองกรอบอีกครั้ง"
                line_bot_api.reply_message(event.reply_token, [
                TextSendMessage(text=txt1),
                TextSendMessage(text=txt2),
                TextSendMessage(text=txt3),
                TextSendMessage(text=txt4)

                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event): 
                if event.message.text == "ขั้นต่อไป":
                    txt = "ไม่มีขั้นต่อไปเเล้วครับ" 
                    line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=txt)])
            
    ##  เเกงเหลืองปลากระพง
    if pred_id == 13 :    
        image_path13 = "https://i.imgur.com/uTNu4sF.jpg" 
        txt1 = f"แกงเหลืองปลากะพง : ช่วยบำรุงร่างกาย รักษาระบบการย่อยอาหารให้ปกติ"           
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path13, preview_image_url=image_path13),TextSendMessage(text=txt1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                
                head1 = f" STEP 1/3 : เตรียมวัตถุดิบ "
                img1 = "https://i.imgur.com/LebAN37.png"
                img2 = "https://i.imgur.com/MxE1TLw.png"
                txt1 = f"ปอกเปลือกสับปะรด"
                txt2 = f"ปอกตาออก"
                
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img2)
                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":
                    head1 = " STEP 2/3 : ต้ม "
                    img1 = "https://i.imgur.com/swe0oMF.png"
                    img2 = "https://i.imgur.com/b4wuIpa.png"
                    txt1 = f"ใส่พริกแกงเหลือง"
                    txt2 = f"ใส่เนื้อปลากะพง"
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
                        head1 = f" STEP  2/3 : ต้ม "
                        img1 = "https://i.imgur.com/GB74C8e.png"
                        img2 = "https://i.imgur.com/5BzuOuK.png"
                        txt1 = f"ใส่สับปะรด"
                        txt2 = f"ปรุงรสด้วยน้ำปลา"
                        
                        line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=head1),
                        TextSendMessage(text=txt1),
                        ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                        TextSendMessage(text=txt2),
                        ImageSendMessage(original_content_url=img2, preview_image_url=img2)          
                        ])
                    else:
                        pass
                    @handler.add(MessageEvent, message=(TextMessage))
                    def handle_text_message(event):
                        if event.message.text == "ขั้นต่อไป":
                            img1 = "https://i.imgur.com/OPapZHS.png"
                            txt1 = f"พร้อมเสิร์ฟเเล้วครับ"
                            line_bot_api.reply_message(event.reply_token, [
                            ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                            TextSendMessage(text=txt1) 
                            ])
                        else:
                            pass
                        @handler.add(MessageEvent, message=(TextMessage))
                        def handle_text_message(event): 
                            if event.message.text == "ขั้นต่อไป":
                                txt = "ไม่มีขั้นต่อไปเเล้วครับ" 
                                line_bot_api.reply_message(event.reply_token, [
                                    TextSendMessage(text=txt)])

    ##  ใบเหลียงผัดไข่   
    if pred_id == 14 :    
        image_path14 = "https://i.imgur.com/5KzhmaC.jpg" 
        txt1 = f"ใบเหลียงผัดไข่ : ช่วยบำรุงสายตา บำรุงผิวพรรณ และมีค่าปริมาณแคลเซียม และฟอสฟอรัสสูง ทำให้ช่วยบำรุงกระดูก และฟันให้แข็งแรง" 
        txt2 = f"ปริมาณโซเดียมสูงมาก  ผู้ป่วยโรคที่เกี่ยวกับความเค็ม ไม่ควรรับประทาน(>>>600 mg ซึ่งเป็นปริมาณโซเดียมปกติใน 1 จาน)"          
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path14, preview_image_url=image_path14),TextSendMessage(text=txt1),TextSendMessage(text=txt2)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                head1 = f" STEP 1/3 : เตรียมใบเหลียงให้เรียบร้อย "
                txt1 = f"เด็ดใบเหลียงเลือกใบที่อ่อนๆ ไม่แข็งกระด้าง ใบที่ใหญ่ให้ฉีกออกแต่ไม่ต้องเล็กมาก ล้างน้ำให้สะอาดพักสะเด็ดน้ำ"
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ])
            else:
                pass
            
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":
                    head1 = f" STEP 2/3 : นําลงไปผัด "
                    txt1 = f"นำน้ำมันใส่กะทะตั้งไฟให้ร้อน เจียวกระเทียมให้หอม ใส่ไข่ไก่ที่ตีไว้ผัดพอไข่เป็นวุ้น"
                    line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=head1),
                        TextSendMessage(text=txt1),
                        ])
                else:
                    pass
                @handler.add(MessageEvent, message=(TextMessage))
                def handle_text_message(event):
                    if event.message.text == "ขั้นต่อไป":
                        head1 = f" STEP 3/3 : จัดเสิร์ฟ "
                        txt1 = f"ใส่ใบเหลียงตามด้วยเครื่องปรุงผัดให้ใบเหลียงพอสลบ ตัดใส่จานทานได้ทันที ใครจะกินกับน้ำพริกกะปิก็เข้ากัน"
                        img1 = "https://i.imgur.com/DorURYU.png"
                        line_bot_api.reply_message(event.reply_token, [
                            TextSendMessage(text=head1),
                            ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                            TextSendMessage(text=txt1),
                            ])
                    else:
                        pass
                    @handler.add(MessageEvent, message=(TextMessage))
                    def handle_text_message(event): 
                        if event.message.text == "ขั้นต่อไป":
                            txt = "ไม่มีขั้นต่อไปเเล้วครับ" 
                            line_bot_api.reply_message(event.reply_token, [
                                TextSendMessage(text=txt)])
                            
    ##  หมูผัดกะปิ      
    if pred_id == 15 :    
        image_path15 = "https://i.imgur.com/WAAuoW2.jpg" 
        txt1 = f"หมูผัดกะปิ : เป็นอาหารประจำถิ่นที่เป็นเอกลักษณ์ของทางใต้"           
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path15, preview_image_url=image_path15),TextSendMessage(text=txt1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                
                head1 = f" STEP 1/3 : โขลกพริกกระเทียม "
                img1 = "https://i.imgur.com/3phmDMk.png"
                img2 = "https://i.imgur.com/XjkzHtn.jpg"
                txt1 = f"ใส่กระเทียมลงไปโขลก"
                txt2 = f"โขลกพริก กระเทียม หอมแดงซอย และกะปิจนเข้ากัน"
                
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img2)
                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":
                    head1 = " STEP 2/3 : ตั้งกะทะ ผัดส่วนผสม "
                    img1 = "https://i.imgur.com/XJzwCLz.jpg"
                    img2 = "https://i.imgur.com/EU1P4j0.png"
                    txt1 = f"นำส่วนผสมที่โขลกไว้ลงไปผัด"
                    txt2 = f"เติมน้ำเปล่าให้มีน้ำขลุกขลิก"
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
                        head1 = f" STEP  3/3 : ปรุงรส "
                        img1 = "https://i.imgur.com/IxziCRq.png"
                        img2 = "https://i.imgur.com/91dxz3a.png"
                        txt1 = f"ใส่ใบมะกรูดตามลงไป"
                        txt2 = f"จัดเสิร์ฟได้เลย"
                        
                        line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=head1),
                        TextSendMessage(text=txt1),
                        ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                        TextSendMessage(text=txt2),
                        ImageSendMessage(original_content_url=img2, preview_image_url=img2)          
                        ])
                    else:
                        pass
                    
                    @handler.add(MessageEvent, message=(TextMessage))
                    def handle_text_message(event): 
                        if event.message.text == "ขั้นต่อไป":
                            txt = "ไม่มีขั้นต่อไปเเล้วครับ" 
                            line_bot_api.reply_message(event.reply_token, [
                                TextSendMessage(text=txt)])  

          
    ##  สะตอผัดกุ้ง  
    if pred_id == 16 :    
        image_path16= "https://i.imgur.com/P8STLYP.jpg"
        txt1 = f"สะตอผัดกุ้ง : ช่วยลดความดันโลหิต ลดน้ำตาลในเลือด ยับยั้งการเจริญเติบโต ของแบคทีเรีย เชื้อรา ช่วยกระตุ้นการบีบตัวของลำไส้ได้อย่างดี"            
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path16, preview_image_url=image_path16),TextSendMessage(text=txt1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                
                
                
                
                txt1 = f"ทำพริกแกงสำหรับผัดสะตอ โดยการใส่กระเทียมลงไปในครก ตามด้วยพริกขี้หนู กะปิ และน้ำตาลปี๊บ โขลกให้ละเอียด ตักใส่ถ้วยพักไว้"
                txt2 = f"นำกระทะตั้งไฟ ความร้อนปานกลาง เทน้ำมันพืชลงไป รอน้ำมันร้อน ใส่พริกแกงที่เตรียมไว้ ผัดจนหอม จากนั้นใส่กุ้งลงไปผัดจนสุก"
                txt3 = f"ใส่สะตอแกะผ่าครึ่ง ผัดจนสุก จากนั้นปรุงรสด้วยน้ำปลา และมะนาวค่ะ ผัดต่อให้เข้ากันดี"
                txt4 = f"พร้อมเสิร์ฟเเล้วครับ"
                img1 = "https://i.imgur.com/B8R6ikw.png"
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=txt1),
                    TextSendMessage(text=txt2),
                    TextSendMessage(text=txt3),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt4)
                    ])
            else:
                pass 

    ##  เเกงไตปลา              
    if pred_id == 17 :    
        image_path17 = "https://i.imgur.com/oZj6CMy.jpg" 
        txt1 = f"แกงไตปลา : ช่วยแก้ท้องอืด รสเผ็ดร้อนของพริกช่วยให้การไหลเวียนโลหิตดีขึ้น มีไขมันจากปลาซึ่งเป็นไขมันดี"           
        line_bot_api.reply_message(event.reply_token, [ImageSendMessage(original_content_url=image_path17, preview_image_url=image_path17),TextSendMessage(text=txt1)])
        @handler.add(MessageEvent, message=(TextMessage))
        def handle_text_message(event):
            if event.message.text == "วิธีการปรุง":
                
                head1 = f" STEP 1/3 : ตำพริกแกงไตปลา "
                img1 = "https://i.imgur.com/YqEhKuz.png"
                img2 = "https://i.imgur.com/LUA8bYk.png"
                txt1 = f"โขลกพริกแห้งให้ละเอียด"
                txt2 = f"ใส่พริกไทยดำที่โขลกแยกไว้"
                
                line_bot_api.reply_message(event.reply_token, [
                    TextSendMessage(text=head1),
                    TextSendMessage(text=txt1),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                    TextSendMessage(text=txt2),
                    ImageSendMessage(original_content_url=img1, preview_image_url=img2)
                    ])
            else:
                pass
            @handler.add(MessageEvent, message=(TextMessage))
            def handle_text_message(event):
                if event.message.text == "ขั้นต่อไป":
                    head1 = " STEP 2/3 : ต้มไตปลา "
                    img1 = "https://i.imgur.com/14ymXEm.png"
                    img2 = "https://i.imgur.com/iACemCP.png"
                    txt1 = f"ต้มไตปลากับสมุนไพรเพิ่อดับกลิ่นคาว"
                    txt2 = f"กรอง"
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
                        head1 = f" STEP  3/3 : ต้มเเกงไตปลา "
                        img1 = "https://i.imgur.com/un5wOX1.png"
                        img2 = "https://i.imgur.com/eLRvita.png"
                        txt1 = f"ใส่มะเขือลงไปต้ม"
                        txt2 = f"ตักใส่ชามเสิร์ฟ"
                        
                        line_bot_api.reply_message(event.reply_token, [
                        TextSendMessage(text=head1),
                        TextSendMessage(text=txt1),
                        ImageSendMessage(original_content_url=img1, preview_image_url=img1),
                        TextSendMessage(text=txt2),
                        ImageSendMessage(original_content_url=img2, preview_image_url=img2)          
                        ])
                    else:
                        pass
                    
                    @handler.add(MessageEvent, message=(TextMessage))
                    def handle_text_message(event): 
                        if event.message.text == "ขั้นต่อไป":
                            txt = "ไม่มีขั้นต่อไปเเล้วครับ" 
                            line_bot_api.reply_message(event.reply_token, [
                                TextSendMessage(text=txt)])
       
             


@app.route('/static/<path:path>')
def send_static_content(path):
    return send_from_directory('static', path)

# create tmp dir for download content
make_static_tmp_dir()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

    
    
