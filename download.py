from bottle import route,get,post,run,static_file,request,response,BaseRequest
import pymongo
import os
"""
@TODO:
    1. check connection status and retry
    2. synchnized visit not supported yet
    3. check owner of pic is one existent email in users collection
"""
conn = pymongo.MongoClient('mongodb://localhost')
db   = conn.pickkick
IP   = '192.168.191.1'
PORT = 8080

class UserManage(object):
    """
    all the operations that manage user information and interacting with database
    """
    field_username = 'username'
    field_email = 'email'
    field_passwd = 'pswd'

    def __init__(self,db):
        self._users = db.users

    def add_one_user(self,username,email,passwd):
        if self._users is None:
            print("Error: Unable to get users collection!")

        if username is None or email is None or passwd is None:
            print('Error: Register incomplete profile')
            return False

        """ forbit duplicate username or email """
        checkDupQuery = {'$or':[{UserManage.field_username:username},{UserManage.field_email:email}]}
        check_res = self._users.find_one(checkDupQuery)

        if check_res is not None:
            return False

        doc = {UserManage.field_username: username,UserManage.field_email:email,UserManage.field_passwd:passwd}
        success=True
        try:
            self._users.insert_one(doc)
            pass
        except Exception as e:
            success=False
            print("Unexpected error:", type(e), e)
        return success

    def checkLogin(self,userInfoDic):
        if userInfoDic is None :
            return False
        if UserManage.field_passwd not in userInfoDic or (UserManage.field_email not in userInfoDic and UserManage.field_username not in userInfoDic):
            return False
        if self._users is None:
            print("Error: Unable to get users collection!")

        success = True
        try:
            doc = self._users.find_one(userInfoDic)
            if doc is None:
                success=False
                pass
            pass
        except Exception as e:
            success = False
            print("Login error:", type(e), e)
        return success

    def deleteOneUser(self,identity):
        if self._users is None:
            print("Error: Unable to get users collection!")

        query = {'$or':[{UserManage.field_username:identity},{UserManage.field_email:identity}]}
        try:
            self._users.delete_one(query)
            pass
        except Exception as e:
            print("Delete user error:", type(e), e)
    
class ImageManage(object):
    """docstring for ImageManage"""
    field_longitute = "longitude"
    field_latitude  = "latitude"
    field_country   = "country"
    field_city      = "city"
    field_time      = "time" 
    field_owner     = "owner"   
    basicInfoSize   = 6

    field_uri       = "uri"
    field_name      = "imgname"

    save_root       = './property/'

    def __init__(self, db):
        self._images = db.images
        
    """
    add one set of image information into db.images collection
    check duplicate before insert is implemented
        1. duplicate according to conflict of field_name  or  field_uri
        2. remove duplicate before insert
    insert dict size must be basicInfoSize + 2
    """
    def add_one_image(self,imageInfoDict):
        if self._images is None:
            print("Error: Unable to get images collection")
            return False

        if not isinstance(imageInfoDict,dict):
            return False

        if len(imageInfoDict) != ImageManage.basicInfoSize+2:  # plus uri
            return False

        checkDupQuery = {'$or':[{ImageManage.field_name:imageInfoDict.get(ImageManage.field_name)},{ImageManage.field_uri:imageInfoDict.get(ImageManage.field_uri)}]}
        
        try:
            """remove the conflict items first if exist"""
            self._images.delete_many(checkDupQuery)
            self._images.insert_one(imageInfoDict)
        except Exception as e:
            print("Error: Insert Image info error.",type(e),e)
            return False
        return True

    def __getUri(self,img_name):
        if not isinstance(img_name,str):
            return None

        query = {ImageManage.field_name:img_name}
        project = {ImageManage.field_uri:1}

        try:
            doc = self._images.find_one(query,project)
        except Exception as e:
            print("Error: Get uri from db by img name error.")
            return None

        return doc.get(ImageManage.field_uri)


    """
    synchronize image items with client
    @param: a set of image names that the client has
    @return: tuple of bool and set of names (client has but db does not)
    """
    def sync(self,img_name_set,owner_name):
        if not isinstance(img_name_set,set):
            return False,None

        query = {ImageManage.field_owner:owner_name} #get only the image names of this owner
        try:
            docs = self._images.find(query,{'_id':0,ImageManage.field_name:1})

        except Exception as e:
            print("Error: retrieve img names error when sync.",type(e),e)
            return False,None

        db_img_name_set = set()
        for doc in docs:
            db_img_name_set.add(doc.get(ImageManage.field_name))

        """delete the documents with field_name that db has but android client does not"""
        unwanted_to_del_set = db_img_name_set - img_name_set

        for name_to_del in unwanted_to_del_set:
            del_query = {ImageManage.field_name:name_to_del}
            try:
                self._images.delete_one(del_query)
                Util.delete_one_file(ImageManage.save_root,name_to_del)
            except Exception as e:
                print("Error: remove error in sync", type(e),e)
                return False,None

        missed_to_inform_set = img_name_set - db_img_name_set

        return True,missed_to_inform_set    

class Util(object):
    """docstring for Util"""
    def __init__(self):
        pass
    
    @staticmethod
    def delete_one_file(root,filename,verbose=True):
        if not isinstance(root,str) or not isinstance(filename,str):
            return False
        
        path = root+filename

        try:
            os.remove(path)
        except Exception as e:
            if verbose:
                print(type(e),e)
        

@post('/sync')
def do_sync():
    name_list = request.forms.get('sync')
    owner     = request.forms.get('owner')
    if name_list is None or owner is None or owner == "" :
        return "false"

    names     = name_list.split(';')

    image_name_set = set()
    for name in names:
        image_name_set.add(name)

    imgManager = ImageManage(db)
    no_err,unnecessary_set = imgManager.sync(image_name_set,owner)

    if not no_err:
        return "false"

    if unnecessary_set is None:
        return "true"
    res = ''
    for name in unnecessary_set:
        res = "{0};{1}".format(res,name)

    return res

       
@get('/download/<filename:path>')
def do_download(filename):
    response = static_file(filename,root = './property/')
    response.set_header('Content-Disposition','attachment; filename=\"'+filename+'\"')
    #filename = request.forms.get('download_file')
    return  response

@post('/uploads')
def do_upload():
    for key in request.headers.keys():
        print(key+': '+request.headers.get(key))

    imgdic = getImageInfoDic(request)
    if len(imgdic) != ImageManage.basicInfoSize:
        print("Error: Missing necessary image infomation")
        return "false"

    print(imgdic)

    upload     = request.files.get('image')
    name, ext = os.path.splitext(upload.filename)
    print('FILE NAME: '+name+ext)

    if ext not in ('.png','.jpg','.jpeg'):
        print('File extension not allowed.')
        return 'false'

    save_path = ImageManage.save_root+upload.filename

    """ remove old file if it's there """
    Util.delete_one_file(ImageManage.save_root,upload.filename,False)

    upload.save(save_path)

    """add other fields and store into mongodb"""
    imgdic[ImageManage.field_uri] = save_path
    imgdic[ImageManage.field_name] = upload.filename
    imgManager = ImageManage(db)
    if not imgManager.add_one_image(imgdic):
        return "False"

    return "True"

    

def getImageInfoDic(request):
    if not isinstance(request,BaseRequest):
        return None

    imageInfo = {}
    
    time       = request.forms.get(ImageManage.field_time)
    if bool(time):
        imageInfo[ImageManage.field_time] = time

    city       = request.forms.get(ImageManage.field_city)
    if bool(city):
        imageInfo[ImageManage.field_city] = city

    country    = request.forms.get(ImageManage.field_country)
    if bool(country):
        imageInfo[ImageManage.field_country] = country

    longitude  = request.forms.get(ImageManage.field_longitute)
    if bool(longitude):
        imageInfo[ImageManage.field_longitute] = longitude

    latitude   = request.forms.get(ImageManage.field_latitude)
    if bool(latitude):
        imageInfo[ImageManage.field_latitude] = latitude

    owner     = request.forms.get(ImageManage.field_owner)
    if bool(owner):
        imageInfo[ImageManage.field_owner] = owner
    return imageInfo

@post('/register')
def do_register():
    query = request.query
    username = query.get(UserManage.field_username)
    email    = query.get(UserManage.field_email)
    passwd   = query.get(UserManage.field_passwd)

    if username is None or username=="" or email is None or email.find('@')==-1 or passwd is None or passwd=="":
        return "false"

    print(username,email,passwd)
    hr = UserManage(db)
    valid = hr.add_one_user(username,email,passwd)

    if valid:
        return 'true'
    else:
        return 'false'

@post('/login')
def do_login():
    query = request.query
    if query is None:
        return "false"

    username = query.get(UserManage.field_username)
    email    = query.get(UserManage.field_email)
    passwd   = query.get(UserManage.field_passwd)

    userInfo = {}
    if bool(username):
        userInfo[UserManage.field_username] = username
    
    if bool(email):
        userInfo[UserManage.field_email] = email

    if bool(passwd):
        userInfo[UserManage.field_passwd] = passwd

    hr = UserManage(db)
    valid = hr.checkLogin(userInfo)

    if valid:
        return 'true'
    else:
        return 'false'

@route('/testpost',method='post')
def test_output():
    clen = request.content_length
    data = request.body.read(clen)
    print(data)
    return 'OK'

@get('/')
def index_page():
    return "<h>You are connected</h>"

if __name__=='__main__':
    # manager = ImageManage(db)
    # dic = {ImageManage.field_latitude: "11111",ImageManage.field_longitute:"22222",ImageManage.field_country:"eu",ImageManage.field_city:"London",ImageManage.field_name:"pic.png",ImageManage.field_uri:"./property/pic.png",ImageManage.field_time:"2015"}
    # manager.add_one_image(dic)
    # manager.add_one_image(dic)
    # hr = UserManage(db)
    # hr.add_one_user('xing','xing@hotmail.com','hsajkdfhksaljdf')

    # if hr.add_one_user('xingchi','xingchij@hotmail.com','hsajkdfhksaljdf'):
    #     print('check fail')
    #     pass

    # hr.deleteOneUser('xingchi')
    # hr.deleteOneUser('xing@hotmail.com')
    # login = {'username':'xingchi','pswd':'hsajkdfhksaljdf'}
    # if hr.checkLogin(login) is True:
    #     print('Success')
    #     pass
    # else:
    #     print('no')
    run(host=IP,port=PORT,debug=True)

