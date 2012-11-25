from qt import *
import sys, getopt
import logging
import random

import ato.db

class MainWindow(QMainWindow):

    def __init__(self, db, *args):
        apply(QMainWindow.__init__, (self, ) + args)
        self.setCaption("Ato - A Tool to remember")
        self.setName("main window")

        self.db = db
        self.item = None

        self.mainWidget=QWidget(self) # dummy widget to contain the
                                      # layout manager
        self.setCentralWidget(self.mainWidget)
        self.mainLayout=QVBoxLayout(self.mainWidget, 5, 5, "main")
        self.buttonLayout=QHBoxLayout(self.mainLayout, 5, "button")
        self.hintsLayout=QHBoxLayout(self.mainLayout, 5, "hints")

        self.bnGetNext=QPushButton("&Next", self.mainWidget, "get next question")
        self.connect(self.bnGetNext, SIGNAL("clicked()"),
                self.slotGetNextQuestion)

        self.bnShowUp=QPushButton("Show &up",
                self.mainWidget, "give up")
        self.connect(self.bnShowUp, SIGNAL("clicked()"),
                self.slotShowUp)

        self.bnGiveUp=QPushButton("&Give up",
                self.mainWidget, "give up")
        self.connect(self.bnGiveUp, SIGNAL("clicked()"),
                self.slotGiveUp)

        self.lbQuestion=QLabel("Question",
                self.mainWidget, "Question")

        self.buttonLayout.addWidget(self.bnGetNext)
        self.buttonLayout.addWidget(self.bnShowUp)
        self.buttonLayout.addWidget(self.bnGiveUp)

        self.mainLayout.addWidget(self.lbQuestion)

        self.__prepareForNext()

    def __prepareForNext(self):
        self.bnGetNext.setEnabled(True)
        self.bnGetNext.setFocus()

        self.bnGiveUp.setEnabled(False)
        self.bnShowUp.setEnabled(False)

    def __prepareForAnswer(self):
        self.bnGetNext.setEnabled(False)

        self.bnGiveUp.setEnabled(True)
        self.bnShowUp.setEnabled(True)

        self.bnShowUp.setFocus()

    def slotGetNextQuestion(self):
        _item = self.db.getNextItem()
        if not _item:
            return

        _question = _item.question()
        self.lbQuestion.setText(_question)
        self.item = _item
        self.__prepareForAnswer()

    def slotGiveUp(self):
        _real_answer = self.item.answer()
        self.item.done(self.db, None)
        self.lbQuestion.setText('Correct answer: %s' % self.item.answer())
        self.__prepareForNext()

    def slotShowUp(self):
        _real_answer = self.item.answer()
        _reply = QMessageBox.question(
                self.mainWidget,
                'Did you think:',
                self.item.answer(),
                QMessageBox.Yes,
                QMessageBox.No)
        if _reply == QMessageBox.Yes:
            self.item.done(self.db)
        else:
            self.item.done(self.db, False)
            self.lbQuestion.setText('Correct answer: %s' % self.item.answer())
        self.__prepareForNext()

def main(args):
    logging.basicConfig(level=logging.DEBUG)
    app=QApplication(args)
    db_file = 'db'
    if len(args) == 2:
      db_file = args[1]
    elif len(args) > 2:
      print "Invalid # of args\nUsage: %s [dbfilename]" % args[0]
      sys.exit(1)

    db = ato.db.DB()
    db.open(db_file)
    win=MainWindow(db)
    win.show()
    app.connect(app, SIGNAL("lastWindowClosed()")
                , app
                , SLOT("quit()")
                )
    app.exec_loop()
    db.close()

if __name__=="__main__":
    main(sys.argv)
