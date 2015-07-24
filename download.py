from bottle import get,post,run,static_file,response


@get('/download/<filename:path>')
def do_download(filename):
    response = static_file(filename,root = './property/')
    response.set_header('Content-Disposition','attachment; filename=\"'+filename+'\"')
    #filename = request.forms.get('download_file')
    return  response

@post('/upload')
def do_upload():
    upload     = request.files.get('image')
    name, ext = os.path.splitext(upload.filename)
    if ext not in ('.png','.jpg','.jpeg'):
        return 'File extension not allowed.'
    save_path = "./property/"+upload.filename
    upload.save(save_path)
    return 'OK'


if __name__=='__main__':
    run(host='localhost',port=8080,debug=True)

