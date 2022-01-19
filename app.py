from operator import sub
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from flask import Flask,render_template,request,flash,redirect,session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
from werkzeug.wrappers import response
import json
from sklearn.metrics.pairwise import cosine_similarity

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_EXTENSIONS1 = { 'jpg'}
def allowed_file1(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS1
app = Flask(__name__)
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER
    
    # Other FLASK config varaibles ...
app.config['SQLALCHEMY_DATABASE_URI']="mysql://root:@localhost/AGH"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SECRET_KEY']="this"

db=SQLAlchemy(app)
class Subject(db.Model):
    subId=db.Column(db.Integer,primary_key=True)
    subject=db.Column(db.String(200),nullable=False)
    marks=db.Column(db.Integer)
    students=db.relationship('Student',backref="students")
    # teachers=db.relationship('Teacher',backref="teacher")

class Student(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    seatNo=db.Column(db.Integer)
    email=db.Column(db.String(200),nullable=False)
    answer=db.Column(db.String(200))
    marks=db.Column(db.Integer)
    subject_id=db.Column(db.Integer,db.ForeignKey('subject.subId'))
    
    


class Teacher(db.Model):
    teacherId=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(200),nullable=False)
    # subject_id=db.Column(db.Integer,db.ForeignKey('subject.subId'))
    
    
class Answer(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    question=db.Column(db.String(200),nullable=False)
    answer=db.Column(db.String(700),nullable=False)
    tid=db.Column(db.Integer,db.ForeignKey('teacher.teacherId'))
    subject_id=db.Column(db.Integer,db.ForeignKey('subject.subId'))
    



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/",methods=['GET','POST'])
def index():
    
    if session.get('messages'):
        s=json.loads(session.get("messages"))
        response=dict(json.loads(session['messages']))
        if s.get('answer'):

            return render_template('index.html',response={"m":response,"message":"success"})

        
        
    else:
        return redirect('/login')
    if request.method=='POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        
        if file.filename == '':
            flash('No selected file')
            
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            path=app.config['UPLOAD_FOLDER']
            
            try:
                if not os.path.exists(path+str(response['seatno'])):
                    os.makedirs(path+str(response['seatno']))
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            
            pdfname = secure_filename(file.filename)
            
            file.save(os.path.join(path+str(response['seatno']),pdfname))
            pdfs = f"uploads/{response['seatno']}/{pdfname}"
            pages = convert_from_path(pdfs, 350, poppler_path = r"C:\Users\HARSH\Downloads\poppler-21.03.0\Library\bin")
            print(pages)
            i = 1
            for page in pages:
                image_name = "Page_" + str(i) + ".jpg"  
                filename = secure_filename(image_name)
                page.save(os.path.join(app.config['UPLOAD_FOLDER']+str(response['seatno']), filename))
                # page.save(image_name, "JPEG")
                i = i+1
            student=Student.query.filter_by(email=response['email']).first()
            print(student.answer)
            student.answer=path+str(response['seatno'])
            db.session.add(student)
            db.session.commit()
            print(student.answer)
            a=json.loads(session['messages']).update({"answer":student.answer})
            session['messages']=a
            return render_template('index.html',response={"m":response,"message":"success"})
    return render_template("index.html",response={"m":response,"message":"upload"})


# @app.route("/login")
# def Login():
#     return render_template("login.html")


@app.route("/login",methods=['GET','POST'])
def login():
    # print('ok')
    if session.get('messages'):
        # print("ok")
        return redirect("/")
    if request.method=='POST':
        if request.form['val']=="2":
            student=Student.query.filter_by(email=request.form['email']).first()
            if not student:
                return redirect(request.url)
            subject=student.subject_id
            answer=student.answer
            session['messages']=json.dumps({"email":student.email,"seatno":student.seatNo,"answer":answer,"subject":subject})
            
            return redirect('/')
        else:
            teacher=Teacher.query.filter_by(email=request.form['email']).first()
            print(teacher)
            if not teacher:
                return redirect(request.url)
            session['messages']=json.dumps({"email":teacher.email,"subject":request.form['subject']})
            print('a')
            return redirect('/teacher')

    return render_template("login.html")




@app.route("/teacher",methods=['GET','POST'])
def teacher():
    # if not session.get('messages'):
    #     return redirect('/login')
        
    # else:
    #     response=json.loads(session['messages'])
    #     subject=Subject.query.filter_by(subject=response['subject']).first()
    #     answ=Answer.query.filter_by(subject_id=subject.subId).first()
    #     if answ:
    #         return render_template("teacher.html",message="yes")
    if request.method=='POST':
        print(request.form)
        subject=Subject.query.filter_by(subject=request.form['subject']).first()
        t=Teacher.query.filter_by(email=response['email']).first()
        i=0
        for key in request.form.keys():
            if i<1:
                i+=1
                continue
            answer=Answer(question=key,answer=request.form[key],subject_id=subject.subId,tid=t.teacherId)
            db.session.add(answer)
            db.session.commit()
            return render_template("teacher.html",message="yes")

    return render_template("teacher.html",message="no")

@app.route("/logout",methods=['GET','POST'])
def logout():
    session.clear()
    return redirect('/login')

# output = "abc"

#VISION API CODE STARTS
def detect_handwritten_ocr(path):
    # """Detects handwritten characters in a local image.

    # Args:
    # path: The path to the local file.
    # """
    import io
    from google.cloud import vision_v1p3beta1 as vision
    import os
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="be-project-314013-465d1bd02408.json"
    client = vision.ImageAnnotatorClient()
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    # Language hint codes for handwritten OCR:
    # en-t-i0-handwrit, mul-Latn-t-i0-handwrit
    # Note: Use only one language hint code per request for handwritten OCR.
    image_context = vision.ImageContext(
        language_hints=['en-t-i0-handwrit'])

    response = client.document_text_detection(image=image,
                                              image_context=image_context)

    # print('Full Text: {}'.format(response.full_text_annotation.text))
    global output
    output = '{}'.format(response.full_text_annotation.text) 
    # for page in response.full_text_annotation.pages:
    #     for block in page.blocks:
    #         print('\nBlock confidence: {}\n'.format(block.confidence))

    #         for paragraph in block.paragraphs:
    #             print('Paragraph confidence: {}'.format(
    #                 paragraph.confidence))

    #             for word in paragraph.words:
    #                 word_text = ''.join([
    #                     symbol.text for symbol in word.symbols
    #                 ])
    #                 print('Word text: {} (confidence: {})'.format(
    #                     word_text, word.confidence))

    #                 for symbol in word.symbols:
    #                     print('\tSymbol: {} (confidence: {})'.format(
    #                         symbol.text, symbol.confidence))

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

# detect_handwritten_ocr('harsh.jpeg')
# # API CODE END


model = SentenceTransformer('bert-base-nli-mean-tokens')

student_arr = []
teacher_arr = []



@app.route("/marks",methods=['GET','POST'])
def marks():
    s=Student.query.filter_by(email=response['email']).first()
    return render_template('marks.html', m=s.marks)
    


@app.route("/grade/<int:no>",methods=['GET','POST'])
def Grade(no):
    if not session.get('messages'):
        return redirect('/login')
    else:
        resp=json.loads(session['messages'])
        # print(type(response))
    location=Student.query.filter_by(seatNo=no).first()
    for i in range(3):
        ans=Answer.query.filter_by(subject_id=resp['subject'], id=i+1).first()
        teacher_arr.append(ans.answer)
    path, dirs, files = next(os.walk(location.answer))
    file_count = len(files)
    dir_list = os.listdir(path)
    for file in dir_list:
        print(file)
        if file_count==0:
            break
        if allowed_file1(file):
            print(location.answer+'/'+file)
            detect_handwritten_ocr(location.answer+'/'+file)
            student_arr.append(output)

        file_count-=1


    teacher_embeddings = model.encode(teacher_arr)
    student_embeddings = model.encode(student_arr)

    
    a= []
    for i in range(len(teacher_arr)):
        a.append(cosine_similarity([teacher_embeddings[i]],student_embeddings[:]))


    similarity_value=[]


    for i in range(len(a)):
        for j in range(len(a[0])):
            for k in range(len(a[0][0])):
                similarity_value.append(a[i][j][k])


    marks =[]

    for i in range(len(teacher_arr)):
        if similarity_value[i] >= 0.9:
            marks.append(3)
        elif similarity_value[i] >= 0.76 and similarity_value[i] < 0.9:
            marks.append(2)
        elif similarity_value[i] >= 0.62 and similarity_value[i] < 0.76:
            marks.append(1)
        else:
            marks.append(0)
    # print(marks[i])
    # print(similarity_value[0])
    # print(similarity_value[1])
    # print(similarity_value[2])
    sum = 0
    for i in range(len(marks)):
        sum = sum + marks[i]
    print(sum)
    print(output)
    # s=Student.query.filter_by(email=response['email']).first()
    # s.marks=sum
    # db.session.add(s)
    # db.session.commit()
    return redirect('/marks')


    


if __name__=="__main__":
    app.run(debug=True)






