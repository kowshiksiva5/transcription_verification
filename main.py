import sys
import os, random
import sqlite3
from sqlite3 import *
from PyQt5.QtWidgets import (QMainWindow,QLineEdit,QApplication,QPushButton,QMessageBox,QLabel)
from PyQt5 import QtMultimedia,QtCore
from PyQt5.QtCore import pyqtSlot
from playsound import playsound
import shutil
import pandas as pd
from pydub import AudioSegment
from pydub.playback import play

df = pd.read_csv('text',names=('filename','transcript'),sep='\t')
# print(df)

def speed_change(sound, speed=1.0):
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
         "frame_rate": int(sound.frame_rate * speed)
      })
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

class App(QMainWindow):
    file = ""
    jobfetchcounter = 0
    fragmentid = ""
    def __init__(self):
        super().__init__()
        self.title = "Transcription Verification Platform"
        self.left = 10
        self.top = 10
        self.width = 1500
        self.height = 200
        self.initUI()


    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.textbox = QLineEdit(self)
        self.textbox.move(20, 20)
        self.textbox.resize(200, 30)
        self.textbox.setPlaceholderText("Enter Name")

        self.phntxt = QLabel(self)
        self.phntxt.move(20, 20)
        self.phntxt.resize(200, 30)
        self.phntxt.setVisible(False)

        self.button = QPushButton('Verify', self)
        self.button.move(300, 20)
        self.button1 = QPushButton("InCorrect", self)
        self.button1.move(300, 105)
        self.button2 = QPushButton("Play Audio", self)
        self.button2.move(15, 105)
        self.button3 = QPushButton("Correct", self)
        self.button3.move(200,105)

        self.fname = QLabel(self)
        self.fname.move(20, 50)
        self.fname.resize(800, 40)
        self.fname.setText("No Job Yet ")

        self.text = QLabel(self)
        self.text.move(20, 70)
        self.text.resize(10000, 40)
        self.text.setText("No Job Yet")

        self.button.clicked.connect(self.on_click)
        self.button2.clicked.connect(self.on_play_click)
        self.button3.clicked.connect(self.mark_correct)
        self.button1.clicked.connect(self.mark_incorrect)

        self.show()
        self.fetch_job()


    @pyqtSlot()
    def on_click(self):
        textboxValue = self.textbox.text()
        conn = self.create_connection()
        verified = textboxValue
        # if(verified):
        QMessageBox.question(self, 'Message', "User Verified - You typed: " + textboxValue, QMessageBox.Ok,
                         QMessageBox.Ok)
        self.phntxt.setText(textboxValue)
        self.button.setVisible(False)
        self.textbox.setVisible(False)
        self.phntxt.setVisible(True)
        self.update()


    @pyqtSlot()
    def on_play_click(self):
        self.play_audio()


    @pyqtSlot()
    def mark_correct(self):
        if self.fname.text() == "":
            QMessageBox.question(self, 'Message', "No Job Found, Please ask for more filesr ", QMessageBox.Ok,
                                 QMessageBox.Ok)
        if self.phntxt.text() == "":
            QMessageBox.question(self, 'Message', "User not verified, please verify User Name", QMessageBox.Ok,
                                 QMessageBox.Ok)
            return 0
        else:
            phoneContributer = self.phntxt.text()
            res = self.mark_job( phoneContributer, "Correct")
            return res


    @pyqtSlot()
    def mark_incorrect(self):
        if (self.phntxt.text() == ""):
            QMessageBox.question(self, 'Message', "User not verified, please verify User Name ", QMessageBox.Ok,
                                 QMessageBox.Ok)
            return 0
        else:
            phoneContributer = self.phntxt.text()
            res = self.mark_job(phoneContributer, "Incorrect")
            return res


    def play_audio(self):
        if(self.file == ""):
            None
        else:
            filename = "audioFiles/source/"+self.file
            fullpath = QtCore.QDir.current().absoluteFilePath(filename)
            try:
                sound  = AudioSegment.from_file(fullpath)
                play(speed_change(sound, 1.25))
            except Exception as e:
                print(e)


    def create_connection(self):
        df = None
        try:
            df = pd.read_csv('text')
        except Error as e:
            print(e)
        return df

    def get_user_from_db(self, conn, phone):
        cur = conn.cursor()
        cur.execute("SELECT * FROM approvers WHERE phoneNumber_approver=? ", (phone,))
        rows = cur.fetchall()

        for row in rows:
            return row[0]

    def get_transcription_from_data(self,df,file):
        try:
            df1 = df.loc[df['filename'] == file]
            # print(df1)
            return df1['transcript'].iloc[0]
        except Exception as e:
            print(e)


    def dailog_submision_success(self):
        mbox = QMessageBox()
        mbox.setText("Submission successful")
        mbox.setStandardButtons(QMessageBox.Ok)
        mbox.exec_()


    def fetch_job(self):
        path, dirs, files = next(os.walk("audioFiles/source"))
        file_count = len(files)
        if file_count > 0:
            filename = random.choice(os.listdir("audioFiles/source"))
            if filename == "":
                self.fname.setText("No Job Yet")
            else:
                self.fname.setText("Job Name: " + filename)
                self.file = filename
                phone = self.phntxt.text()
                transcription = self.get_transcription_from_data(df,filename.split('.wav')[0])
                print(transcription)
                if transcription is None:
                    self.text.setText("No Transcription Yet")
                    self.jobfetchcounter +=1
                    if self.jobfetchcounter > 5:
                        print("Unable to get valid source")
                        self.fname.setText("No valid source ")
                        self.text.setText("No valid source ")
                        self.update()
                        return
                    else:
                        print(self.jobfetchcounter)
                        print("Getting next job")
                        self.fetch_job()
                        self.update()
                else:
                    self.jobfetchcounter = 0
                    self.text.setText("Transcription: " + transcription)
                return [filename,phone,transcription]
        else:
            self.fname.setText("No source Yet")
            self.text.setText("No source Yet")

        return None


    def mark_job(self,phone,job_state):
        conn = self.create_connection()
        task = (phone,self.fragmentid)
        if job_state == "Incorrect":
            self.move_incorrect_file(self.text.text())
        else:
            self.move_file(self.text.text())
        return self.update()


    def move_incorrect_file(self,transcription):
        sourcefilename = self.fname.text().split(":")[1].strip()
        filename = "audioFiles/source/" + sourcefilename
        newPath = "audioFiles/Incorrect/" + sourcefilename
        fullpath = QtCore.QDir.current().absoluteFilePath(filename)
        newPath =QtCore.QDir.current().absoluteFilePath(newPath)
        shutil.move(fullpath, newPath)
        txtfilename = sourcefilename + ".txt"
        completeName = os.path.join("audioFiles/Incorrect/", txtfilename)
        f = open(completeName, "w")
        f.write(transcription)
        f.close()
        self.fetch_job()


    def move_file(self,transcription):
        sourcefilename = self.fname.text().split(":")[1].strip()
        filename = "audioFiles/source/" + sourcefilename
        newPath = "audioFiles/completed/" + sourcefilename
        fullpath = QtCore.QDir.current().absoluteFilePath(filename)
        newPath =QtCore.QDir.current().absoluteFilePath(newPath)
        shutil.move(fullpath, newPath)
        txtfilename = sourcefilename + ".txt"
        completeName = os.path.join("audioFiles/completed/", txtfilename)
        f = open(completeName, "w")
        f.write(transcription)
        f.close()
        self.fetch_job()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())