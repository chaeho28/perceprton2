import os
import uuid
import flask
import urllib
from PIL import Image
from tensorflow.keras.models import load_model
from flask import Flask , render_template  , request , send_file
from tensorflow.keras.preprocessing.image import load_img , img_to_array

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model = load_model(os.path.join(BASE_DIR , 'keras_model.h5'))


ALLOWED_EXT = set(['jpg' , 'jpeg', 'png', 'jfif'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXT

classes=['C-130', 'CIVIL', 'E737', 'F-16', 'F-35', 'F-5_[JAEGONG]', 'KAI_T-50', 'KC-330_[CYGNUS]', 'KF-21', 'KOREA_AIR_DEFENSE', 'f-15']
#클래스의 순서는 틀리면 안 됨. + 별도의 csv 라벨링으로 처리 가능
#모델 생성시 클래스 순서를 활용해야 함.
def predict(filename , model):
    img = load_img(filename , target_size = (224, 224)) #모델의 입력망 크기 입력공간1
    img = img_to_array(img)
    img = img.reshape(1,224,224,3)#모델의 입력망 크기 입력공간2 (1과 3은 옵션으로 X)

    img = img.astype('float32')
    img = img/255.0
    result = model.predict(img)

    dict_result = {}
    for i in range(11):#분류할 클래스 수 배치 
        dict_result[result[0][i]] = classes[i]

    res = result[0]
    res.sort()
    res = res[::-1]
    prob = res[:3]
    
    prob_result = []
    class_result = []
    for i in range(3): #예측한 값의 상위 3개까지 표시==>html 인덱스 값을 5개로 설정
        prob_result.append((prob[i]*100).round(5))
        class_result.append(dict_result[prob[i]])

    return class_result, prob_result




@app.route('/')
def home():
        return render_template("index.html")

@app.route('/success' , methods = ['GET' , 'POST'])
def success():
    error = ''
    target_img = os.path.join(os.getcwd() , 'static/images')
    if request.method == 'POST':
        if(request.form):
            link = request.form.get('link')
            try :
                resource = urllib.request.urlopen(link)
                unique_filename = str(uuid.uuid4())
                filename = unique_filename+".jpg"
                img_path = os.path.join(target_img , filename)
                output = open(img_path , "wb")
                output.write(resource.read())
                output.close()
                img = filename

                class_result , prob_result = predict(img_path , model)

                predictions = {
                      "class1":class_result[0],
                        "class2":class_result[1],
                        "class3":class_result[2],
                        "prob1": prob_result[0],
                        "prob2": prob_result[1],
                        "prob3": prob_result[2],
                }

            except Exception as e : 
                print(str(e))
                error = '형식에 맞지 않는 이미지입니다. 확인부탁드립니다.'

            if(len(error) == 0):
                return  render_template('success.html' , img  = img , predictions = predictions)
            else:
                return render_template('index.html' , error = error)  #예측링크가 아닐 경우의 표시

            
        elif (request.files):
            file = request.files['file']
            if file and allowed_file(file.filename):
                file.save(os.path.join(target_img , file.filename))
                img_path = os.path.join(target_img , file.filename)
                img = file.filename

                class_result , prob_result = predict(img_path, model)

                predictions = { #예측 클라스 값 상위 5개 전달
                      "class1":class_result[0],
                        "class2":class_result[1],
                        "class3":class_result[2],
                        "prob1": prob_result[0],
                        "prob2": prob_result[1],
                        "prob3": prob_result[2],
                }

            else:
                error = "'jpg' , 'jpeg', 'png', 'jfif' 형식만 제출해주세요-!"

            if(len(error) == 0):
                return  render_template('success.html' , img  = img , predictions = predictions)
            else:
                return render_template('index.html' , error = error)

    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(debug = True)


