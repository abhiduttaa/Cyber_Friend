from flask import Flask, render_template,url_for,redirect
import threading
import uuid
app = Flask(__name__)

result={}

def task(task_id):
    print("reached task function")
    import time
    print("started task...")
    time.sleep(5)
    print("task completed...")
    result[task_id]="task is done finally!"
    print(result[task_id])



@app.route('/')
def home():
    print("reached home")
    task_id = str(uuid.uuid4())
    print("task_id:",task_id)
    #task(task_id)
    threading.Thread(target=task, args={task_id}).start()
    print("threading done")
    print(threading.current_thread().name)
    return redirect(url_for('check_result',task_id=task_id))


@app.route('/chk_result/<task_id>')
def check_result(task_id):
    print("reached check_result")
    result1=result.get(task_id)
    if not result1:
        return render_template('test_ui.html',result="in progress")
    return render_template('test_ui.html',result=result1)

if __name__=='__main__':
    app.run(debug=True)