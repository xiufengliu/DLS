import schedule
import time

from app import db

def batchJob1Min():
    try:
        result = db.session.execute("select script from essex_job_que where seg_type=1 and next_execute_time<=now()")
        scripts = result.fetchall()
        if scripts:
            for row in scripts:
                sqlStatements = row[0].split(";")
                for sql in sqlStatements:
                    db.session.execute(sql)
            db.session.execute(
                "update essex_job_que set next_execute_time=now()+interval'%s' where seg_type=1 and next_execute_time<=now()" % '1minutes')
            db.session.commit()
        else:
            print('No pending jobs')
    except Exception as e:
        print(e)

def batchJob10Min():
    try:
        result = db.session.execute("select script from essex_job_que where  seg_type=3 and next_execute_time<=now()")
        scripts = result.fetchall()
        if scripts:
            for row in scripts:
                sqlStatements = row[0].split(";")
                for sql in sqlStatements:
                    db.session.execute(sql)
            db.session.execute(
                "update essex_job_que set next_execute_time=now()+interval'%s' where  seg_type=3 and next_execute_time<=now()" % '10minutes')
            db.session.commit()
        else:
            print('No pending jobs')
    except Exception as e:
        print(e)



#schedule.every().hour.do(job)
#schedule.every().day.at("10:30").do(job)
#schedule.every().monday.do(job)
#schedule.every().wednesday.at("13:15").do(job)

class Job:
    def __init__(self):
        self.started = False
        schedule.every(1).minutes.do(batchJob1Min)
        schedule.every(10).minutes.do(batchJob10Min)


    def stop(self):
        self.started = False

    def start(self):
        if self.started:
            return
        else:
            self.started = True
            while self.started:
                schedule.run_pending()
                time.sleep(1)

    def status(self):
        return 'Running' if self.started else 'Stopped'

job = Job()