# -*- coding: utf-8 -*-
from __future__ import print_function

import datetime
import shutil
import sqlite3
import sys
import threading

import pytz
import telebot
from flask import Flask, render_template
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pyngrok import ngrok

# =====================================================================================================================
# см. README.md

bot_token =
owner =
folder =

# =====================================================================================================================

bot = telebot.TeleBot(bot_token)
bot.remove_webhook()
markdown = """
    *bold text*
    _italic text_
    [text](URL)
    """
ssh_tunnel = ngrok.connect(302, "http")

dbUsers=sqlite3.connect('users.db', check_same_thread=False)
dbU=dbUsers.cursor()
dbStats=sqlite3.connect('stats.db', check_same_thread=False)
dbS=dbStats.cursor()
dbTasks=sqlite3.connect('tasks.db', check_same_thread=False)
dbT=dbTasks.cursor()

dbT.execute('''CREATE TABLE IF NOT EXISTS "allTasks" (
	"taskID"	INTEGER,
	"taskText"	TEXT,
	"taskAnswer"	TEXT,
	"teacherID"	INTEGER,
	"taskTime"	TEXT
, "fileID"	TEXT)''')
dbTasks.commit()
dbT.execute('''CREATE TABLE IF NOT EXISTS "tasks" (
	"taskID"	INTEGER,
	"taskText"	TEXT,
	"taskAnswer"	TEXT
, "fileID"	INTEGER)''')
dbTasks.commit()
dbU.execute('''CREATE TABLE IF NOT EXISTS "users" (
	"id"	INTEGER,
	"name"	TEXT,
	"teacher"	INTEGER
)''')
dbUsers.commit()

dbU.execute('SELECT id FROM users WHERE (teacher LIKE 1)')
Teachers=dbU.fetchall()
dbU.execute('SELECT id FROM users WHERE (teacher LIKE 0)')
Students=dbU.fetchall()
dbU.execute('SELECT name FROM users WHERE (teacher LIKE 1)')
TeachersNames=dbU.fetchall()
dbU.execute('SELECT name FROM users WHERE (teacher LIKE 0)')
StudentsNames=dbU.fetchall()
dbT.execute("SELECT * FROM allTasks")
allTasks=dbT.fetchall()
print(Teachers)

teacher=[]
tchr_names=[]
students=[]
std_names=[]
std_stat=[]
stat_local=[]
statlc=''
globalstat=[]
for tchr in Teachers:
    tchr=str(tchr[0])
    if tchr!='\n':
        if '\n' in tchr:
            tchr=tchr[:-1]
        teacher.append(int(tchr))
oldtchr=teacher.copy()
teacher.sort()
c=-1
for tchr in TeachersNames:
    tchr = tchr[0]
    c+=1
    if tchr!='\n':
        if '\n' in tchr:
            tchr=tchr[:-1]
        stdid=teacher.index(oldtchr[c])
        tchr_names.insert(stdid,tchr)
for std in Students:
    std=str(std[0])
    if std != '\n':
        if '\n' in std:
            std=std[:-1]
        students.append(int(std))
oldstd=students.copy()
students.sort()
c=-1
for stdname in StudentsNames:
    c+=1
    stdname=stdname[0]
    if stdname != '\n':
        if '\n' in stdname:
            stdname=stdname[:-1]
        stdid=students.index(oldstd[c])
        std_names.insert(stdid,str(stdname))

Stats=[]
for std in students:
    std=str(std)
    dbS.execute('SELECT * FROM "{}"'.format(std))
    Stats.append(dbS.fetchall())
for tchr in teacher:
    std=str(tchr)
    dbS.execute('SELECT * FROM "{}"'.format(std))
    Stats.append(dbS.fetchall())

std_stat=Stats

dbT.execute('SELECT * FROM tasks')
taskList=dbT.fetchall()
tasks=[]

b=''
task=''; answer='';wait_right_answer=False; taskcount=0; taskdate=""
pic=None; tchr=''; oldans=False; numofrenamingstd=0; numofrenamingtchr=0
otvetanet=[False]*len(students); taskid=0; numofuserstat=0; mainid=0
ispic=False; countoftasks=0; lastClosed=True; picsended=False; mainid_pic=0
geninprocess=0; call2gen=''
usersinactivity={}
for std in students:
    usersinactivity[std]=False
for std in teacher:
    usersinactivity[std]=False
stat_local=[]
for i in range(len(std_stat)):
    stat_local.append([''])

users=[]
for std in students:
    users.append(std)
for tchr in teacher:
    users.append(tchr)

auth={}
for std in students:
    auth[std]=False

cancel=telebot.types.InlineKeyboardMarkup()
cancel.add(telebot.types.InlineKeyboardButton(text='Отмена \U000021A9', callback_data='cncl'))

yesNo=telebot.types.InlineKeyboardMarkup()
yesNo.row(
    telebot.types.InlineKeyboardButton(text='Да', callback_data='1'),
    telebot.types.InlineKeyboardButton(text='Нет', callback_data='0')
)
yesNo.row(
    telebot.types.InlineKeyboardButton(text='Отмена \U000021A9', callback_data='cncl')
)

taskGen=telebot.types.InlineKeyboardMarkup()
taskGen.row(
    telebot.types.InlineKeyboardButton(text='Выбрать шаблон из базы данных \U0001F4E4',
                                       callback_data='taskdb')
)
taskGen.row(
    telebot.types.InlineKeyboardButton(text='Изменить условие \U0001F4DD',
                                       callback_data='changetxt'),
    telebot.types.InlineKeyboardButton(text='Изменить ответ \U00002611',
                                       callback_data='changeans')
)
taskGen.row(
    telebot.types.InlineKeyboardButton(text='Добавить картинку \U0001F305',
                                       callback_data='addpic'),
    telebot.types.InlineKeyboardButton(text='Удалить картинку \U0001F305',
                                       callback_data='delpic')
)
taskGen.row(
    telebot.types.InlineKeyboardButton(text='Готово \U00002705',
                                       callback_data='gentskdone')
)
taskGen.row(
    telebot.types.InlineKeyboardButton(text='Отменить \U000021A9',
                                       callback_data='cncl')
)


startMenu=telebot.types.InlineKeyboardMarkup()
startMenu.row(
    telebot.types.InlineKeyboardButton(text="Ученики \U0001F465",
                                       callback_data="students")
)
startMenu.row(
    telebot.types.InlineKeyboardButton(text="Задания \U0001F4DD",
                                       callback_data="tasks")
)

stdMenu=telebot.types.InlineKeyboardMarkup()
stdMenu.row(
    telebot.types.InlineKeyboardButton(text="Управление \U0001F4CD",
                                       callback_data="stdManagement")
)
stdMenu.row(
    telebot.types.InlineKeyboardButton(text="Статистика \U0001F4CA",
                                       callback_data="stdStats")
)
stdMenu.row(
    telebot.types.InlineKeyboardButton(text='Отменить \U000021A9',
                                       callback_data='cncl')
)

stdManagement=telebot.types.InlineKeyboardMarkup()
stdManagement.row(
    telebot.types.InlineKeyboardButton(text="Посмотреть список \U0001F4C4",
                                       callback_data='liststd')
)
stdManagement.row(
    telebot.types.InlineKeyboardButton(text="Переименовать \U0000270F",
                                       callback_data='renamestd')
)
stdManagement.row(
    telebot.types.InlineKeyboardButton(text="Удалить \U0000274C",
                                       callback_data='removestd')
)
stdManagement.row(
    telebot.types.InlineKeyboardButton(text='Отменить \U000021A9',
                                       callback_data='cncl')
)

stdStats=telebot.types.InlineKeyboardMarkup()
stdStats.row(
    telebot.types.InlineKeyboardButton(text='Посмотреть общую статистику \U0001F440',
                                       callback_data='statstd')
)
stdStats.row(
    telebot.types.InlineKeyboardButton(text='Посмотреть статистику пользователя \U0001F464',
                                       callback_data='userstatstd')
)
stdStats.row(
    telebot.types.InlineKeyboardButton(text='Разослать статистику \U0001F4E9',
                                       callback_data='sendstatstd')
)
stdStats.row(
    telebot.types.InlineKeyboardButton(text='Отменить \U000021A9',
                                       callback_data='cncl')
)

tskMenu=telebot.types.InlineKeyboardMarkup(row_width=1)
tskMenu.add(
    telebot.types.InlineKeyboardButton(text="Отправить задание \U0001F4E9",
                                       callback_data='sendtsk'),
    telebot.types.InlineKeyboardButton(text="Закрыть последнее задание \U0001F512",
                                           callback_data='closetsk'),
    telebot.types.InlineKeyboardButton(text="Работа с базой данных \U0001F4DD",
                                       callback_data='workdbtsk'),
    telebot.types.InlineKeyboardButton(text='Отменить \U000021A9',
                                           callback_data='cncl')
)

tskSend=telebot.types.InlineKeyboardMarkup(row_width=1)
tskSend.add(
    telebot.types.InlineKeyboardButton(text='Создать новое задание \U00002795',
                                       callback_data='sendnewtsk'),
    telebot.types.InlineKeyboardButton(text='Выбрать существующее из бд \U0001F4E4',
                                       callback_data='importtsk'),
    telebot.types.InlineKeyboardButton(text='Отменить \U000021A9',
                                           callback_data='cncl')
)

importtsk=telebot.types.InlineKeyboardMarkup(row_width=1)
importtsk.add(
    telebot.types.InlineKeyboardButton(text='Готово \U00002705',
                                       callback_data='gentskdone'),
    telebot.types.InlineKeyboardButton(text='Выбрать другое задание \U0001F504',
                                                   callback_data='importtsk'),
    telebot.types.InlineKeyboardButton(text='Отменить \U000021A9',
                                                   callback_data='cncl')
)

tskWorkDb=telebot.types.InlineKeyboardMarkup(row_width=1)
tskWorkDb.add(
    telebot.types.InlineKeyboardButton(text='Посмотреть базу данных \U0001F440',
                                               callback_data='seedbtsk'),
    telebot.types.InlineKeyboardButton(text='Создать новое задание \U00002795',
                                           callback_data='dbaddtsk'),
    telebot.types.InlineKeyboardButton(text='Редактировать существующее задание \U0000270F',
                                               callback_data='dbedittsk'),
    telebot.types.InlineKeyboardButton(text='Отменить \U000021A9',
                                               callback_data='cncl')
)


tskTimeSend=telebot.types.InlineKeyboardMarkup(row_width=1)
tskTimeSend.add(
    telebot.types.InlineKeyboardButton(text='Отправить сейчас \U0001F4E9',
                                                   callback_data='sendnowtsk'),
    telebot.types.InlineKeyboardButton(text='Запланировать отправку \U0001F552',
                                                       callback_data='sendlatertsk'),
    telebot.types.InlineKeyboardButton(text='Отменить \U000021A9',
                                        callback_data='cncl')
)

startstdMenu=telebot.types.InlineKeyboardMarkup(row_width=1)
startstdMenu.add(
    telebot.types.InlineKeyboardButton(text='Моя статистика \U0001F4CA',
                                       callback_data='mystat'),
    telebot.types.InlineKeyboardButton(text='Задания \U0001F4D2',
                                     callback_data='stdmytasks')
)

stdMyTasks=telebot.types.InlineKeyboardMarkup(row_width=1)
stdMyTasks.add(
    telebot.types.InlineKeyboardButton(text="Ответить сейчас \U0001F4DD",
                                       callback_data='stdansnow'),
    telebot.types.InlineKeyboardButton(text="Вернуться в меню \U000021A9",
                                           callback_data='returntomenu'),
)

def sendMenu(id):
    if id in teacher:
        bot.send_message(id,"Выберите объект для работы:",reply_markup=startMenu,
                         disable_notification=True)
    else:
        bot.send_message(id, "Выберите действие:", reply_markup=startstdMenu,
                         disable_notification=True)
    return


def updusers():
    users = []
    for std in students:
        users.append(std)
    for tchr in teacher:
        users.append(tchr)
@bot.callback_query_handler(func=lambda call: call.data=='cncl')
def cncl(call):
    global geninprocess
    global users
    global task
    global answer
    global ispic
    global mainid
    global mainid_pic
    global picsended
    global pic
    bot.answer_callback_query(callback_query_id=call.id, text='Действие отменено')
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    finishCheckInactivity(call.message.chat.id)
    if call.message.chat.id == geninprocess:
        geninprocess=0
        task=''
        answer=''

        if picsended:
            bot.delete_message(call.message.chat.id, mainid_pic)
        ispic=False
        picsended=False
        pic=None
        bot.edit_message_text("Действие отменено.", call.message.chat.id, mainid)

    else:
        bot.edit_message_text("Действие отменено.", call.message.chat.id, call.message.message_id)
    sendMenu(call.message.chat.id)



@bot.callback_query_handler(func=lambda call: call.data=='students')
def stdMenuCall(call):
    bot.edit_message_text(text="Выберите далее",reply_markup=stdMenu,
                          message_id=call.message.message_id,
                          chat_id=call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data=='stdManagement')
def stdManagementCall(call):
    bot.edit_message_text(text="Выберите действие",reply_markup=stdManagement,
                          message_id=call.message.message_id,
                          chat_id=call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data=='stdStats')
def stdStatsCall(call):
    bot.edit_message_text(text="Выберите действие",reply_markup=stdStats,
                          message_id=call.message.message_id,
                          chat_id=call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data=='liststd')
def liststdCall(call):
    msg='*Список учеников*\n\n'
    for std in range(len(students)):
        msg+= str(std+1) + ') '+ std_names[std] + ' _('+str(students[std])+')_\n'
    bot.edit_message_text(text=msg, parse_mode='markdown',
                          message_id=call.message.message_id,
                          chat_id=call.message.chat.id)
    sendMenu(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data=='renamestd')
def renamestdCall(call):
    msg=call.message
    bot.delete_message(call.message.chat.id,
                                  call.message.message_id)
    renamestd(msg)

@bot.callback_query_handler(func=lambda call: call.data=='removestd')
def removestdCall(call):
    msg = call.message
    bot.delete_message(call.message.chat.id,
                       call.message.message_id)
    removestudent(msg)

@bot.callback_query_handler(func=lambda call: call.data=='statstd')
def statstdCall(call):
    msg = call.message
    bot.delete_message(call.message.chat.id,
                       call.message.message_id)
    printstat(msg)

@bot.callback_query_handler(func=lambda call: call.data=='userstatstd')
def userstatstdCall(call):
    msg = call.message
    bot.delete_message(call.message.chat.id,
                       call.message.message_id)
    listuserstat(msg)

@bot.callback_query_handler(func=lambda call: call.data=='sendstatstd')
def sendstatstdCall(call):
    msg = call.message
    bot.delete_message(call.message.chat.id,
                       call.message.message_id)
    countsendstats(msg)

@bot.callback_query_handler(func=lambda call: call.data=='tasks')
def taskMenuCall(call):
    bot.edit_message_text("Выберите далее",call.message.chat.id,call.message.message_id,
                          reply_markup=tskMenu)

@bot.callback_query_handler(func=lambda call: call.data=='sendtsk')
def sendtskCall(call):
    bot.edit_message_text("Выберите действие", call.message.chat.id, call.message.message_id,
                          reply_markup=tskSend)

@bot.callback_query_handler(func=lambda call: call.data=='closetsk')
def closetskCall(call):
    msg = call.message
    bot.delete_message(call.message.chat.id,
                       call.message.message_id)
    closelasttask(msg)
    sendMenu(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data=='workdbtsk')
def workdbtskCall(call):
    bot.edit_message_text("Выберите действие", call.message.chat.id, call.message.message_id,
                          reply_markup=tskWorkDb)

@bot.callback_query_handler(func=lambda call: call.data=='sendnewtsk')
def sendNewtskCall(call):
    global call2gen
    msg = call.message
    bot.delete_message(call.message.chat.id,
                       call.message.message_id)
    call2gen='sendnew'
    gen_task(msg)

@bot.callback_query_handler(func=lambda call: call.data=='importtsk')
def importtskCall(call):
    global geninprocess
    if geninprocess != 0:
        bot.send_message(call.message.chat.id, "Генератор заданий занят. Вы будете уведомлены, когда он освободится")
        threading.Thread(target=notificationFreeGen(call.message.chat.id)).start()
        return
    geninprocess = call.message.chat.id
    bot.delete_message(call.message.chat.id,
                       call.message.message_id)
    previd=sendSite(call.message.chat.id,
             'taskslist', 'База данных',
             "Введите ID задания из базы данных")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id,sendImporttsk,*[previd])
def sendImporttsk(message,previd):
    global task; global ispic; global pic; global answer; global mainid_pic; global picsended; global mainid
    global geninprocess; global call2gen
    ispic=False
    bot.edit_message_reply_markup(message.chat.id,previd)
    tskid = int(message.text)
    dbT.execute('SELECT * FROM tasks WHERE taskID="{}"'.format(tskid))
    tsk = dbT.fetchall()[0]
    task = tsk[1]
    answer = tsk[2]
    if tsk[3] != None:
        pic = tsk[3]
        ispic = True
    msg=changeGenTaskMsg("*Хотите отправить данное задание?*")
    call2gen='sendnew'
    if not ispic:
        botmsg=bot.send_message(message.chat.id,msg,reply_markup=importtsk,parse_mode='markdown')
        mainid = botmsg.message_id
    else:
        botmsg=bot.send_message(message.chat.id, msg,  parse_mode='markdown')
        botpic=bot.send_photo(message.chat.id,pic,reply_markup=importtsk)
        mainid_pic = botpic.message_id
        mainid=botmsg.message_id
        picsended = True

@bot.callback_query_handler(func=lambda call: call.data=='gentskdone')
def gentskDoneCall(call):
    global call2gen; global task; global answer; global ispic; global pic;global mainid; global geninprocess
    global mainid_pic; global picsended
    if call2gen=='sendnew':
        if ispic:
            bot.delete_message(call.message.chat.id, mainid_pic)
            picsended = False
        bot.edit_message_text("Когда хотите отправить задание?",call.message.chat.id,
                              mainid, reply_markup=tskTimeSend)
    elif call2gen=='addnew':
        callSaveTask(call)
    elif 'editdb' in call2gen:
        tskid=int(call2gen[6:])
        finishCheckInactivity(call.message.chat.id)
        if ispic:
            dbT.execute('UPDATE tasks SET taskText="{}", taskAnswer="{}", fileID="{}" WHERE taskID="{}"'.format(
                task,answer,pic,tskid
            ))
            dbTasks.commit()
        else:
            dbT.execute('UPDATE tasks SET taskText="{}", taskAnswer="{}", fileID="{}" WHERE taskID="{}"'.format(
                task, answer, None,tskid
            ))
            dbTasks.commit()

        bot.edit_message_text("Задание успешно обновлено", call.message.chat.id,
                              mainid, parse_mode='markdown')
        geninprocess = 0
        task = ''
        answer = ''
        if ispic:
            bot.delete_message(call.message.chat.id, mainid_pic)
        ispic = False
        pic = None
        picsended = False
        sendMenu(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data=='sendnowtsk')
def sendnowtskCall(call):
    global ispic
    global pic
    msg=changeGenTaskMsg("*Отправка задания*")
    bot.edit_message_text(msg,call.message.chat.id,
                          call.message.message_id,
                          parse_mode='markdown')
    if ispic:
        bot.send_photo(call.message.chat.id,
                       pic)
    callSendTask(call)

@bot.callback_query_handler(func=lambda call: call.data=='seedbtsk')
def seeDBtskCalll(call):
    bot.delete_message(call.message.chat.id,
                       call.message.message_id)
    sendSite(call.message.chat.id,'taskslist','База данных заданий','Просмотр базы данных',True)
    sendMenu(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data=='dbaddtsk')
def dbAddtskCall(call):
    global call2gen
    msg = call.message
    bot.delete_message(call.message.chat.id,
                       call.message.message_id)
    call2gen = 'addnew'
    gen_task(msg)

@bot.callback_query_handler(func=lambda call: call.data=='dbedittsk')
def dbEdittskCall(call):
    bot.delete_message(call.message.chat.id,
                       call.message.message_id)
    previd = sendSite(call.message.chat.id,
                      'taskslist', 'База данных',
                      "Введите ID задания из базы данных")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, editImporttsk, *[previd])
def editImporttsk(message,previd):
    global task
    global ispic
    global pic
    global answer
    global call2gen
    bot.edit_message_reply_markup(message.chat.id, previd)
    tskid = int(message.text)
    dbT.execute('SELECT * FROM tasks WHERE taskID="{}"'.format(tskid))
    tsk = dbT.fetchall()[0]
    task = tsk[1]
    answer = tsk[2]
    if tsk[3] != None:
        pic = tsk[3]
        ispic = True
    call2gen = 'editdb' + str(tskid)
    gen_task(message)


@bot.callback_query_handler(func=lambda call: call.data=='stdmytasks')
def stdMyTasksCall(call):
    if len(tasks)==0:
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text= "Нет заданий без ответа")
        sendMenu(call.message.chat.id)
        return
    if not isInListCortege(tasks[-1][4], stat_local[uid(call.message.chat.id)]):
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="Вы не ответили на задание")
        if tasks[-1][5] != None:
            bot.send_message(call.message.chat.id,
                             tasks[-1][1])
            bot.send_photo(call.message.chat.id, tasks[-1][5],
                           reply_markup=stdMyTasks)
        else:
            bot.send_message(call.message.chat.id,
                             tasks[-1][1], reply_markup=stdMyTasks)
    else:
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text="Нет заданий без ответа")
        sendMenu(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data=='returntomenu')
def returnToMenuCall(call):
    bot.delete_message(call.message.chat.id,
                       call.message.message_id)
    sendMenu(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data=='stdansnow')
def stdAnsNowCall(call):
    bot.edit_message_reply_markup(call.message.chat.id,
                                  call.message.message_id)
    bot.send_message(call.message.chat.id,
                     "Введите ответ на задание")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id,
                                              wait_answer)

@bot.callback_query_handler(func=lambda call: call.data=='mystat')
def myStatCall(call):
    msg = call.message
    bot.delete_message(call.message.chat.id,
                       call.message.message_id)
    countmystat(msg)


@bot.callback_query_handler(func=lambda call: call.data == '1')
def yes(call):
    if call.message.text=='Желаете прикрепить картинку?':
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, cancel)
        bot.edit_message_text("Пришлите мне картинку",
                              call.message.chat.id, call.message.message_id,
                              reply_markup=cancel)
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, send_pic, *[call.message.message_id])

@bot.callback_query_handler(func=lambda call: call.data == '0')
def no(call):
    if call.message.text=='Желаете прикрепить картинку?':
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, cancel)
        bot.edit_message_text("Введите правильный ответ на задание",
                              call.message.chat.id, call.message.message_id,
                              reply_markup=cancel)
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, right_answer, *[call.message.message_id])

@bot.callback_query_handler(func=lambda call: call.data == 'taskdb')
def callTaskDB(call):
    previd=sendSite(call.message.chat.id,'taskslist','База Данных заданий','Введите ID задания из базы данных')
    startCheckInactivity(call.message.chat.id)
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, chooseTaskID, *[previd])
def chooseTaskID(message,previd):
    global task
    global answer
    global pic
    global ispic
    global picsended

    id=int(message.text)
    tsk=dbT.execute('SELECT * FROM tasks WHERE taskID="{}"'.format(id)).fetchall()[0]

    task=tsk[1]
    answer=tsk[2]
    if tsk[3]!=None:
        ispic = True
        pic=tsk[3]

    editGenTaskMsg(message.chat.id,previd,message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == 'changetxt')
def callChangeTXT(call):
    botmsg=bot.send_message(call.message.chat.id,'Введите условие задания')
    previd=botmsg.message_id
    startCheckInactivity(call.message.chat.id)
    bot.register_next_step_handler_by_chat_id(call.message.chat.id,changeTaskText,*[previd])
def changeTaskText(message,previd):
    global task
    global mainid
    task=message.text
    editGenTaskMsg(message.chat.id,previd,message.message_id)
    return

@bot.callback_query_handler(func=lambda call: call.data == 'changeans')
def callChangeAns(call):
    botmsg=bot.send_message(call.message.chat.id,'Введите ответ на задание')
    previd=botmsg.message_id
    startCheckInactivity(call.message.chat.id)
    bot.register_next_step_handler_by_chat_id(call.message.chat.id,changeTaskAnswer,*[previd])
def changeTaskAnswer(message,previd):
    global answer
    global mainid
    answer=message.text
    editGenTaskMsg(message.chat.id,previd,message.message_id)
    return


@bot.callback_query_handler(func=lambda call: call.data == 'addpic')
def callAddPic(call):
    botmsg = bot.send_message(call.message.chat.id, 'Отправьте картинку, которую хотите добавить.')
    previd = botmsg.message_id
    startCheckInactivity(call.message.chat.id)
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, addTaskPic, *[previd])
def addTaskPic(message, previd):
    global pic
    global ispic
    global mainid
    global mainid_pic
    global picsended
    pic=message.photo[0].file_id
    if ispic:
        bot.delete_message(message.chat.id, mainid_pic)
        picsended = False
        bot.edit_message_reply_markup(message.chat.id, mainid, reply_markup=taskGen)
    ispic=True

    editGenTaskMsg(message.chat.id,previd,message.message_id)
    return

@bot.callback_query_handler(func=lambda call: call.data == 'delpic')
def callDelPic(call):
    global mainid_pic
    global mainid
    global ispic
    global picsended
    if not ispic:
        bot.answer_callback_query(callback_query_id=call.id, text='Картинка отсутствует')
        return
    bot.delete_message(call.message.chat.id,mainid_pic)
    ispic=False
    picsended=False
    bot.edit_message_text(changeGenTaskMsg(), call.message.chat.id, mainid,
                          reply_markup=taskGen,
                          parse_mode="Markdown")
    bot.answer_callback_query(callback_query_id=call.id, text='Картинка удалена')
    return


@bot.callback_query_handler(func=lambda call: call.data == 'sendtsk')
def callSendTask(call):
    global answer
    global task
    global ispic
    global taskcount
    global taskdate
    global tchr
    global otvetanet
    global taskid
    global lastClosed
    global mainid
    global picsended
    global geninprocess
    taskcount += 1
    dbT.execute('SELECT taskID FROM tasks WHERE taskText="{}" AND taskAnswer="{}"'.format(task,answer))
    exists = dbT.fetchall()
    finishCheckInactivity(call.message.chat.id)
    if not exists:
        dbT.execute('SELECT * FROM tasks')
        lastID = (dbT.fetchall())[-1][0]
        if ispic:
            dbT.execute('INSERT INTO tasks VALUES("{}","{}","{}","{}")'.format(lastID + 1, task, answer, pic))
        else:
            dbT.execute('INSERT INTO tasks VALUES("{}","{}","{}",NULL)'.format(lastID + 1, task, answer))
        dbTasks.commit()
        if ispic:
            uploadfile(pic)
        dbT.execute('SELECT taskID FROM tasks WHERE taskText="{}"'.format(task))
        taskid = dbT.fetchall()[0][0]
        taskList.append((taskid, task, answer))
    else:
        taskid = exists[0][0]
    taskdate = str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13]
    if ispic:
        dbT.execute('INSERT INTO allTasks VALUES("{}","{}","{}","{}","{}","{}")'.format(taskid, task, answer, tchr, taskdate, pic))
    else:
        dbT.execute('INSERT INTO allTasks VALUES("{}","{}","{}","{}","{}",NULL)'.format(taskid, task, answer, tchr, taskdate))
    dbTasks.commit()
    msgg = tchr_names[teacher.index(tchr)] + " отправил вам задание"
    otvetanet = [False] * len(students)
    tasks.append((taskid, task, answer, tchr, taskdate, pic))
    allTasks.append((taskid, task, answer, tchr, taskdate, pic))
    lastClosed = False
    for std in students:
        bot.clear_step_handler_by_chat_id(chat_id=std)

        if ispic:
            bot.send_message(std, msgg + '\n\n' + task)
            bot.send_photo(std, pic,
                           reply_markup=stdMyTasks)
        else:
            bot.send_message(std, msgg + '\n\n' + task,
                             reply_markup=stdMyTasks)
    ispic=False
    picsended=False
    geninprocess=False
    bot.send_message(call.message.chat.id, "Рассылка успешно завершена")

@bot.callback_query_handler(func=lambda call: call.data == 'savetsk2db')
def callSaveTask(call):
    global answer
    global task
    global ispic
    global tchr
    global otvetanet
    global taskid
    global lastClosed
    global mainid
    global picsended
    global geninprocess
    dbT.execute(
        'SELECT taskID FROM tasks WHERE taskText="{}" AND taskAnswer="{}"'.format(task, answer))
    exists = dbT.fetchall()

    finishCheckInactivity(call.message.chat.id)
    if not exists:
        dbT.execute('SELECT * FROM tasks')
        lastID = (dbT.fetchall())[-1][0]
        dbT.execute('INSERT INTO tasks VALUES("{}","{}","{}","{}")'.format(lastID + 1, task, answer, pic))
        dbTasks.commit()
        if ispic:
            uploadfile(pic)
        dbT.execute('SELECT taskID FROM tasks WHERE taskText="{}"'.format(task))
        taskid = dbT.fetchall()[0][0]
        taskList.append((taskid, task, answer))
    else:
        taskid = exists[0][0]
        ispic = False
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
        picsended = False
        geninprocess = False
        bot.send_message(call.message.chat.id, "Данное задание уже существует. Его ID - "+str(taskid))
        return
    ispic = False
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    picsended = False
    geninprocess = False

    bot.send_message(call.message.chat.id, "Задание успешно сохранено. Его ID - "+str(taskid))

def editGenTaskMsg(id,previd,delid):
    global ispic; global pic
    global mainid; global picsended
    global mainid_pic
    startCheckInactivity(id)
    bot.delete_message(id, delid)
    bot.delete_message(id, previd)
    msg=changeGenTaskMsg()

    if ispic:

        bot.edit_message_text(msg, id, mainid,
                              parse_mode="Markdown")
        if not picsended:
            botmsg=bot.send_photo(id,pic,reply_markup=taskGen)
            picsended=True
            mainid_pic=botmsg.message_id
    else:
        bot.edit_message_text(msg, id, mainid,
                            reply_markup=taskGen,
                            parse_mode="Markdown")
    return


def changeGenTaskMsg(header='*Генератор заданий*'):
    global task
    global answer
    global ispic
    global pic
    global mainid
    ispic1=''
    if not ispic:
        ispic1 = "_Отсутствует_"
    if task == '':
        task = '_Отсутствует_'
    if answer == '':
        answer = '_Отсутствует_'
    msg = '''
{}\n
*Условие:*    {}\n
*Ответ:*    {}\n
*Изображение:*    {}\n
        '''.format(header,
                   task,
                   answer,
                   ispic1)
    return msg

def notificationFreeGen(id):
    global geninprocess
    while True:
        if geninprocess==0:
            bot.send_message(id,"Генератор заданий освободился")
            return

urlpc=0; urlcc=0

def sendSite(id,site='',btn_text='URL',msg="URL",justsee=False):
    sendURL = telebot.types.InlineKeyboardMarkup(row_width=1)
    url=str(ssh_tunnel.public_url)+'/'+site
    if not justsee:
        sendURL.add(
            telebot.types.InlineKeyboardButton(text=btn_text,url=url),
            telebot.types.InlineKeyboardButton(text='Отменить \U000021A9',
                                               callback_data='cncl')
        )
    else:
        sendURL.add(
            telebot.types.InlineKeyboardButton(text=btn_text, url=url)
        )

    botmsg=bot.send_message(id,msg,reply_markup=sendURL, parse_mode="Markdown")
    previd=botmsg.message_id
    return previd

def uid(id):
    return users.index(id)
def provcommands(a):
    if a[0]=='/':
        return False
    return True
def stat(id,clearing=False,count=0):
    mes=""
    if count==0:
        for k in stat_local:
            try:
                k.remove('')
            except:
                continue
        for tsk in stat_local:
            try:

                for arg in tsk:

                    dbU.execute('SELECT name FROM users WHERE id="{}"'.format(arg[0]))
                    username=dbU.fetchall()[0][0]

                    dbT.execute('SELECT taskText FROM tasks WHERE taskID="{}"'.format(arg[1]))
                    tsktext=dbT.fetchall()[0][0]

                    dbS.execute('SELECT timeTask FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
                    tskdate = dbS.fetchall()[0][0]

                    dbS.execute('SELECT timeAnswer FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
                    anstime = dbS.fetchall()[0][0]

                    dbS.execute('SELECT isRight FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
                    isright = dbS.fetchall()[0][0]

                    dbS.execute('SELECT answer FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
                    userans = dbS.fetchall()[0][0]

                    dbT.execute('SELECT taskAnswer FROM tasks WHERE taskID="{}"'.format(arg[1]))
                    tskans = dbT.fetchall()[0][0]

                    mes=mes + ("\n\n*" + str(username) + "*"
                               +"\n*Текст задания:*    " + str(tsktext)
                               +"\n*Было задано:*    "+ str(tskdate)
                               +"\n*Время сдачи:*    "+ str(anstime))
                    if isright==1:
                        mes=mes+("\n*Правильность:*    Верно")

                    elif isright==0:
                        mes = mes + ("\n*Правильность:*    Неверно"
                                     +"\n*Ответ пользователя:*    "+userans
                                     +"\n*Правильный ответ:*    "+tskans)
            except:
                continue


        if clearing:
            glstatwrite = open('Stat.txt', 'w')
            glstatwrite.write(mes)
            glstatwrite.close()
            sendSite(id,'localstat','Статистика',
                     "Резервная копия статистики будет отправлена в формате txt. Её также можно посмотреть по ссылке ниже",
                     True)
            bot.send_document(id, open('Stat.txt'))
            return
    else:
        for k in stat_local:
            try:
                k.remove('')
            except:
                continue

        for std in stat_local:
            try:
                for tsknum in range(len(std)-1,len(std)-1-count,-1):

                    arg=std[tsknum]
                    dbU.execute('SELECT name FROM users WHERE id="{}"'.format(arg[0]))
                    username = dbU.fetchall()[0][0]

                    dbT.execute('SELECT taskText FROM tasks WHERE taskID="{}"'.format(arg[1]))
                    tsktext = dbT.fetchall()[0][0]

                    dbS.execute('SELECT timeTask FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
                    tskdate = dbS.fetchall()[0][0]

                    dbS.execute('SELECT timeAnswer FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
                    anstime = dbS.fetchall()[0][0]

                    dbS.execute('SELECT isRight FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
                    isright = dbS.fetchall()[0][0]

                    dbS.execute('SELECT answer FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
                    userans = dbS.fetchall()[0][0]

                    dbT.execute('SELECT taskAnswer FROM tasks WHERE taskID="{}"'.format(arg[1]))
                    tskans = dbT.fetchall()[0][0]

                    mes = mes + ("\n\n*" + str(username) + "*"
                                 + "\n*Текст задания:*    " + str(tsktext)
                                 + "\n*Было задано:*    " + str(tskdate)
                                 + "\n*Время сдачи:*    " + str(anstime))
                    if isright == 1:
                        mes = mes + ("\n*Правильность:*    Верно")
                    elif isright == 0:
                        mes = mes + ("\n*Правильность:*    Неверно"
                                     + "\n*Ответ пользователя:*    " + userans
                                     + "\n*Правильный ответ:*    " + tskans)
            except:
                continue

    try:
        sendSite(id,'localstat','Статистика', mes, True)
    except:
        if mes=='':
            bot.send_message(id, "Статистика пуста", parse_mode="Markdown")
        else:
            glstatwrite=open('Stat.txt','w')
            glstatwrite.write(mes)
            glstatwrite.close()
            sendSite(id, 'localstat', 'Статистика',
                     "Резервная копия статистики будет отправлена в формате txt. Её также можно посмотреть по ссылке ниже",
                     True)
            bot.send_document(id,open('Stat.txt'))

def userStat(id,stdid,count=1,msg='',clearing=False):
    global lastClosed
    isstd = id in students
    if stdid in students:
        std = students.index(stdid)

    else:
        std=teacher.index(stdid)+len(students)
    mes = msg
    if count!=0:

        c=0
        for k in stat_local:
            try:
                k.remove('')
            except:
                continue
        for tk in range(len(stat_local[std])-1,len(stat_local[std])-1-count,-1):
            try:
                tsk=stat_local[std][tk]
            except:

                userStat(id,stdid,0,msg)
                return
            if c==count:
                break
            c+=1
            arg=tsk
            dbU.execute('SELECT name FROM users WHERE id="{}"'.format(arg[0]))
            username = dbU.fetchall()[0][0]

            dbT.execute('SELECT taskText FROM tasks WHERE taskID="{}"'.format(arg[1]))
            tsktext = dbT.fetchall()[0][0]

            dbS.execute('SELECT timeTask FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            tskdate = dbS.fetchall()[0][0]

            dbS.execute('SELECT timeAnswer FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            anstime = dbS.fetchall()[0][0]

            dbS.execute('SELECT isRight FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            isright = dbS.fetchall()[0][0]

            dbS.execute('SELECT answer FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            userans = dbS.fetchall()[0][0]

            dbT.execute('SELECT taskAnswer FROM tasks WHERE taskID="{}"'.format(arg[1]))
            tskans = dbT.fetchall()[0][0]

            mes = mes + ("\n"
                        + "\n*Текст задания:*    " + str(tsktext)
                        + "\n*Было задано:*    " + str(tskdate)
                        + "\n*Время сдачи:*    " + str(anstime))
            if c==1 and isstd and not lastClosed:
                mes = mes + ("\n_Результат временно скрыт_")
                continue
            if isright == 1:
                mes = mes + ("\n*Правильность:*    Верно")
            elif isright == 0:
                mes = mes + ("\n*Правильность:*    Неверно"
                             + "\n*Ответ пользователя:*    " + userans
                             + "\n*Правильный ответ:*    " + tskans)

        if clearing:
            glstatwrite = open('UserStat.txt', 'w')
            glstatwrite.write(mes)
            glstatwrite.close()
            bot.send_message(id, "Резервная копия статистики пользователя будет отправлена в формате txt.")
            bot.send_document(id, open('UserStat.txt'))
            return

        try:

            if mes!=msg:
                bot.send_message(id, mes, parse_mode="Markdown")
            else:
                bot.send_message(id, "Статистика данного пользователя пуста", parse_mode="Markdown")
        except:
            if mes == msg:
                bot.send_message(id, "Статистика данного пользователя пуста", parse_mode="Markdown")
            else:
                glstatwrite = open('UserStat.txt', 'w')
                glstatwrite.write(mes)
                glstatwrite.close()
                bot.send_message(id, "Статистика слишком большая для сообщения.\nОна будет отправлена в формате txt.")
                bot.send_document(id, open('UserStat.txt'))
    else:

        for k in stat_local:
            try:
                k.remove('')
            except:
                continue
        c=0
        for arg in stat_local[std]:
            c+=1
            dbU.execute('SELECT name FROM users WHERE id="{}"'.format(arg[0]))
            username = dbU.fetchall()[0][0]

            dbT.execute('SELECT taskText FROM tasks WHERE taskID="{}"'.format(arg[1]))
            tsktext = dbT.fetchall()[0][0]

            dbS.execute('SELECT timeTask FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            tskdate = dbS.fetchall()[0][0]

            dbS.execute('SELECT timeAnswer FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            anstime = dbS.fetchall()[0][0]

            dbS.execute('SELECT isRight FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            isright = dbS.fetchall()[0][0]

            dbS.execute('SELECT answer FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            userans = dbS.fetchall()[0][0]

            dbT.execute('SELECT taskAnswer FROM tasks WHERE taskID="{}"'.format(arg[1]))
            tskans = dbT.fetchall()[0][0]
            mes = mes + ("\n\n*" + str(username) + "*"
                         + "\n*Текст задания:*    " + str(tsktext)
                         + "\n*Было задано:*    " + str(tskdate)
                         + "\n*Время сдачи:*    " + str(anstime))
            if c==1 and isstd and not lastClosed:
                mes = mes + ("\n_Результат временно скрыт_")
                continue
            if isright == 1:
                mes = mes + ("\n*Правильность:*    Верно")
            elif isright == 0:
                mes = mes + ("\n*Правильность:*    Неверно"
                             + "\n*Ответ пользователя:*    " + userans
                             + "\n*Правильный ответ:*    " + tskans)
        try:

            if mes != msg:
                bot.send_message(id, mes, parse_mode="Markdown")
            else:
                bot.send_message(id, "Статистика данного пользователя пуста", parse_mode="Markdown")
        except:

            if mes == msg:
                bot.send_message(id, "Статистика данного пользователя пуста", parse_mode="Markdown")
            else:
                glstatwrite = open('UserStat.txt', 'w')
                glstatwrite.write(mes)
                glstatwrite.close()
                bot.send_message(id,
                                 "Статистика слишком большая для сообщения.\nОна будет отправлена в формате txt.")
                bot.send_document(id, open('UserStat.txt'))
def globstat(id,clearing=False):
    global dbStats, dbS
    global dbTasks, dbT
    mes=""
    if clearing:
        for std in students:
            dbS.execute('SELECT * FROM "{}"'.format(std))
            mes+=str(dbS.fetchall())
        for std in teacher:
            dbS.execute('SELECT * FROM "{}"'.format(std))
            mes+=str(dbS.fetchall())
        glstatwrite = open('GlobalStat.txt', 'w')
        glstatwrite.write(mes)
        glstatwrite.close()
        dbT.execute('SELECT * FROM allTasks')
        mes = str(dbT.fetchall())
        gltaskwrite = open('Tasks.txt', 'w')
        gltaskwrite.write(mes)
        gltaskwrite.close()
        backuptime=str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13].replace(' ','-').replace(':','-')
        backupstat=open(r'backups\stats-{}.db'.format(backuptime),'w')
        backuptask = open(r'backups\tasks-{}.db'.format(backuptime), 'w')

        backupstat.close()
        backuptask.close()
        shutil.copy(r'stats.db',r'backups\stats-{}.db'.format(backuptime))
        shutil.copy(r'tasks.db', r'backups\tasks-{}.db'.format(backuptime))

        bot.send_message(id, "Резервная копия статистики будет отправлена в формате txt.")
        bot.send_document(id, open('GlobalStat.txt'))
        bot.send_document(id, open('Tasks.txt'))
        return
    for k in std_stat:
        try:
            k.remove('')
        except:
            continue
    for std in std_stat:
        try:
            for arg in std:

                dbU.execute('SELECT name FROM users WHERE id="{}"'.format(arg[0]))
                username = dbU.fetchall()[0][0]

                dbT.execute('SELECT taskText FROM tasks WHERE taskID="{}"'.format(arg[1]))
                tsktext = dbT.fetchall()[0][0]

                dbS.execute('SELECT timeTask FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
                tskdate = dbS.fetchall()[0][0]

                dbS.execute('SELECT timeAnswer FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
                anstime = dbS.fetchall()[0][0]

                dbS.execute('SELECT isRight FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
                isright = dbS.fetchall()[0][0]

                dbS.execute('SELECT answer FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
                userans = dbS.fetchall()[0][0]

                dbT.execute('SELECT taskAnswer FROM tasks WHERE taskID="{}"'.format(arg[1]))
                tskans = dbT.fetchall()[0][0]

                mes = mes + ("\n\n*" + str(username) + "*"
                             + "\n*Текст задания:*    " + str(tsktext)
                             + "\n*Было задано:*    " + str(tskdate)
                             + "\n*Время сдачи:*    " + str(anstime))
                if isright == 1:
                    mes = mes + ("\n*Правильность:*    Верно")
                elif isright == 0:
                    mes = mes + ("\n*Правильность:*    Неверно"
                                 + "\n*Ответ пользователя:*    " + userans
                                 + "\n*Правильный ответ:*    " + tskans)
        except:
            continue

    try:
        bot.send_message(id, mes, parse_mode="Markdown")
    except:
        if mes=='':
            bot.send_message(id, "Статистика пуста", parse_mode="Markdown")
        else:
            glstatwrite=open('GlobalStat.txt','w')
            glstatwrite.write(mes)
            glstatwrite.close()
            bot.send_message(id,"Статистика слишком большая для сообщения.\nОна будет отправлена в формате txt.")
            bot.send_document(id,open('GlobalStat.txt'))

def userGlobalStat(id,stdid,count=1,msg='',clearing=0):
    global lastClosed
    isstd=id in students
    if stdid in students:
        std=students.index(stdid)
    else:
        std=teacher.index(stdid)+len(students)

    mes = msg
    if count!=0:

        c=0
        for k in std_stat:
            try:
                k.remove('')
            except:
                continue
        for tk in range(len(std_stat[std])-1,len(std_stat[std])-1-count,-1):
            try:
                tsk=std_stat[std][tk]
            except:

                userGlobalStat(id,stdid,0,msg)
                return
            if c==count:
                break

            c+=1
            arg=tsk
            dbU.execute('SELECT name FROM users WHERE id="{}"'.format(arg[0]))
            username = dbU.fetchall()[0][0]

            dbT.execute('SELECT taskText FROM tasks WHERE taskID="{}"'.format(arg[1]))
            tsktext = dbT.fetchall()[0][0]

            dbS.execute('SELECT timeTask FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            tskdate = dbS.fetchall()[0][0]

            dbS.execute('SELECT timeAnswer FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            anstime = dbS.fetchall()[0][0]

            dbS.execute('SELECT isRight FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            isright = dbS.fetchall()[0][0]

            dbS.execute('SELECT answer FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            userans = dbS.fetchall()[0][0]

            dbT.execute('SELECT taskAnswer FROM tasks WHERE taskID="{}"'.format(arg[1]))
            tskans = dbT.fetchall()[0][0]
            mes = mes + ("\n"
                         + "\n*Текст задания:*    " + str(tsktext)
                         + "\n*Было задано:*    " + str(tskdate)
                         + "\n*Время сдачи:*    " + str(anstime))
            if c==1 and isstd and not lastClosed:
                mes = mes + ("\n_Результат временно скрыт_")
                continue

            if isright == 1:
                mes = mes + ("\n*Правильность:*    Верно")
            elif isright == 0:
                mes = mes + ("\n*Правильность:*    Неверно"
                             + "\n*Ответ пользователя:*    " + userans
                             + "\n*Правильный ответ:*    " + tskans)
        if clearing:
            glstatwrite = open('UserGlobalStat.txt', 'w')
            glstatwrite.write(mes)
            glstatwrite.close()
            bot.send_message(id, "Резервная копия статистики пользователя будет отправлена в формате txt.")
            bot.send_document(id, open('UserGlobalStat.txt'))
            return
        try:

            if mes!=msg:
                bot.send_message(id, mes, parse_mode="Markdown")
            else:
                bot.send_message(id, "Статистика данного пользователя пуста", parse_mode="Markdown")
        except:
            if mes == msg:
                bot.send_message(id, "Статистика данного пользователя пуста", parse_mode="Markdown")
            else:
                glstatwrite = open('UserGlobalStat.txt', 'w')
                glstatwrite.write(mes)
                glstatwrite.close()
                bot.send_message(id, "Статистика слишком большая для сообщения.\nОна будет отправлена в формате txt.")
                bot.send_document(id, open('UserGlobalStat.txt'))
    else:

        for k in std_stat:
            try:
                k.remove('')
            except:
                continue
        c=0
        for arg in std_stat[std]:
            c+=1
            dbU.execute('SELECT name FROM users WHERE id="{}"'.format(arg[0]))
            username = dbU.fetchall()[0][0]

            dbT.execute('SELECT taskText FROM tasks WHERE taskID="{}"'.format(arg[1]))
            tsktext = dbT.fetchall()[0][0]

            dbS.execute('SELECT timeTask FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            tskdate = dbS.fetchall()[0][0]

            dbS.execute('SELECT timeAnswer FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            anstime = dbS.fetchall()[0][0]

            dbS.execute('SELECT isRight FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            isright = dbS.fetchall()[0][0]

            dbS.execute('SELECT answer FROM "{}" WHERE timeTask="{}"'.format(arg[0], arg[3]))
            userans = dbS.fetchall()[0][0]

            dbT.execute('SELECT taskAnswer FROM tasks WHERE taskID="{}"'.format(arg[1]))
            tskans = dbT.fetchall()[0][0]

            mes = mes + ("\n\n*" + str(username) + "*"
                         + "\n*Текст задания:*    " + str(tsktext)
                         + "\n*Было задано:*    " + str(tskdate)
                         + "\n*Время сдачи:*    " + str(anstime))
            if c==1 and isstd and not lastClosed:
                mes = mes + ("\n_Результат временно скрыт_")
                continue
            if isright == 1:
                mes = mes + ("\n*Правильность:*    Верно")
            elif isright == 0:
                mes = mes + ("\n*Правильность:*    Неверно"
                             + "\n*Ответ пользователя:*    " + userans
                             + "\n*Правильный ответ:*    " + tskans)
        if clearing:
            glstatwrite = open('UserGlobalStat.txt', 'w')
            glstatwrite.write(mes)
            glstatwrite.close()
            bot.send_message(id, "Резервная копия статистики пользователя будет отправлена в формате txt.")
            bot.send_document(id, open('UserGlobalStat.txt'))
            return
        try:

            if mes != msg:
                bot.send_message(id, mes, parse_mode="Markdown")
            else:
                bot.send_message(id, "Статистика данного пользователя пуста", parse_mode="Markdown")
        except:

            if mes == msg:
                bot.send_message(id, "Статистика данного пользователя пуста", parse_mode="Markdown")
            else:

                glstatwrite = open('UserGlobalStat.txt', 'w')
                glstatwrite.write(mes)
                glstatwrite.close()
                bot.send_message(id,
                                 "Статистика слишком большая для сообщения.\nОна будет отправлена в формате txt.")
                bot.send_document(id, open('UserGlobalStat.txt'))

def isInListCortege(elem,list_of_corteges):
    for crtg in list_of_corteges:
        if elem in crtg:
            return True
    return False


def provcheck():
    global taskcount
    global taskid
    global allTasks
    for k in stat_local:
        try:
            k.remove('')
        except:
            continue
    for std in range(len(std_stat)):
        if len(stat_local[std])<taskcount:
            for tsk in range(len(allTasks)):

                if not isInListCortege(allTasks[tsk][4],std_stat[std]):
                    try:
                        std_stat[std].append((students[std], allTasks[tsk][0],
                                                   "Нет ответа", allTasks[tsk][4],
                                                   "Нет ответа", -1))
                        dbS.execute('INSERT INTO "{}" VALUES("{}","{}","{}","{}","{}","{}")'.format(students[std],
                                                                                               students[std],
                                                                                                   allTasks[tsk][0],
                                                                                                   "Нет ответа",
                                                                                                   allTasks[tsk][4],
                                                                                                   "Нет ответа",-1))
                        dbStats.commit()
                    except:
                        continue
    for std in range(len(students)):
        if len(stat_local[std]) < taskcount:
            for tsk in range(len(tasks)):
                if not isInListCortege(tasks[tsk][4],stat_local[std]):
                    otvetanet[std] = True
                    stat_local[std].append((students[std], tasks[tsk][0],
                                                     "Нет ответа", tasks[tsk][4],
                                                     "Нет ответа", -1))


def inactivity(id):
    global geninprocess
    global users
    global task
    global answer
    global ispic
    global mainid
    global mainid_pic
    global pic
    global picsended
    bot.clear_step_handler_by_chat_id(id)
    if id == geninprocess:
        geninprocess = 0
        task = ''
        answer = ''
        bot.edit_message_reply_markup(id, mainid)
        if ispic:
            bot.delete_message(id, mainid_pic)
        ispic = False
        pic = None
        picsended = False
    bot.send_message(id, "Вы бездействовали более 10 минут, задача была автоматически отменена")
    return

def startCheckInactivity(id):
    try:
        usersinactivity[id].cancel()
        usersinactivity[id]=threading.Timer(600.0, lambda: inactivity(id))
    except:
        usersinactivity[id] = threading.Timer(600.0, lambda: inactivity(id))
    usersinactivity[id].start()
    return
def finishCheckInactivity(id):
    try:
        usersinactivity[id].cancel()
        return
    except:
        return


# ======================================================================================================================

insertdb='INSERT INTO users VALUES ('
@bot.message_handler(commands=['start'],content_types=['photo','text','sticker','file'])
def start_message(message):  # СТАРТ
    global f
    global insertdb
    try:
        if message.chat.id in students or message.chat.id in teacher:
            bot.send_message(message.chat.id, text="Вы уже зарегистрированы")
            return
        insertdb+=str(message.chat.id)+', '
        bot.send_message(message.chat.id, text="Введите, пожалуйста, свою фамилию и имя")
        bot.register_next_step_handler_by_chat_id(message.chat.id, FI)
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
          '\n', sys.exc_info())
def FI(message):
    global insertdb
    try:
        users.append(message.chat.id)
        students.append(message.chat.id)
        students.sort()
        updusers()
        stdind=students.index(message.chat.id)
        fi=str(message.text)
        std_names.insert(stdind,fi)
        insertdb +="'"+ str(fi)+"'" + ', 0)'
        dbU.execute(insertdb)
        dbUsers.commit()
        std_stat.insert(stdind,[])
        stat_local.insert(stdind,[])
        dbS.execute('''CREATE TABLE IF NOT EXISTS "{}"("userID"	INTEGER,
                    "taskID"	INTEGER COLLATE NOCASE,
                    "timeAnswer"	TEXT, 
                    "timeTask"	TEXT ,
                     "answer"	TEXT,
                    "isRight"	INTEGER)'''.format(message.chat.id))
        dbStats.commit()
        otvetanet.insert(stdind,False)
        bot.send_message(message.chat.id, "Вы успешно зарегистрированы")
        msgowner="Зарегистрирован новый пользователь\n"+str(fi)+' ('+ str(message.chat.id) +')'
        bot.send_message(owner,msgowner)
        insertdb = 'INSERT INTO users VALUES ('
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n', sys.exc_info())


@bot.message_handler(commands=['addtask'],content_types=['photo','text','sticker','file'])
def gen_task(message):
    global mainid; global mainid_pic
    global geninprocess
    global picsended

    if message.chat.id in teacher or message.chat.id==owner:
        if geninprocess!=0:
            bot.send_message(message.chat.id,"Генератор заданий занят. Вы будете уведомлены, когда он освободится")
            threading.Thread(target=notificationFreeGen(message.chat.id)).start()


            return
        geninprocess=message.chat.id
        msg=changeGenTaskMsg()
        if not ispic:
            botmsg=bot.send_message(message.chat.id,msg,reply_markup=taskGen,
                             parse_mode="Markdown")
        else:
            botmsg = bot.send_message(message.chat.id, msg,
                                      parse_mode="Markdown")
            botpic = bot.send_photo(message.chat.id,pic,reply_markup=taskGen)
            mainid_pic=botpic.message_id
            picsended = True
        mainid=botmsg.message_id
        startCheckInactivity(message.chat.id)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
        return



@bot.message_handler(commands=['oldsend'],content_types=['photo','text','sticker','file'])
def send_task(message):
    global task
    global wait_right_answer
    global taskcount
    global tchr
    global pic
    global ispic
    try:
    # for k in range(1):
        if message.chat.id==owner or message.chat.id in teacher:
            tchr = message.chat.id
            ispic = False
            pic=None
            task=message.text[6:]
            if task=='':
                bot.send_message(tchr, "Пожалуйста, вводите после /send текст задания")
                return

            bot.send_message(tchr, "Желаете прикрепить картинку?",reply_markup=yesNo)
        else:
            bot.send_message(message.chat.id,"У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
                  '\n', sys.exc_info())

def send_pic(message, previd):
    try:
        bot.edit_message_reply_markup(message.chat.id, previd)
        global pic
        global ispic
        ispic=True
        pic=message.photo[0].file_id
        botmsg=bot.send_message(message.chat.id, "Введите правильный ответ на задание",reply_markup=cancel)
        previd=botmsg.message_id
        bot.register_next_step_handler_by_chat_id(message.chat.id, right_answer,*[previd])
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())

def right_answer(message,previd):
    global answer
    global task
    global ispic
    global taskcount
    global taskdate
    global tchr
    global otvetanet
    global taskid
    global lastClosed
    try:
    # for k in range(1):
        bot.edit_message_reply_markup(message.chat.id, previd)
        if message.chat.id==owner or message.chat.id in teacher:
            provcheck()
            answer=message.text
            taskcount+=1
            dbT.execute('SELECT taskID FROM tasks WHERE taskText="{}"'.format(task))
            exists = dbT.fetchall()

            if not exists:
                dbT.execute('SELECT * FROM tasks')
                lastID=(dbT.fetchall())[-1][0]
                dbT.execute('INSERT INTO tasks VALUES("{}","{}","{}","{}")'.format(lastID+1,task,answer,pic))
                dbTasks.commit()

                dbT.execute('SELECT taskID FROM tasks WHERE taskText="{}"'.format(task))
                taskid=dbT.fetchall()[0][0]
                taskList.append((taskid, task, answer))
            else:
                taskid=exists[0][0]
            taskdate=str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13]
            dbT.execute('INSERT INTO allTasks VALUES("{}","{}","{}","{}","{}","{}")'.format(taskid, task, answer,tchr,taskdate,pic))
            dbTasks.commit()
            msgg = tchr_names[teacher.index(tchr)] + " отправил вам задание"
            otvetanet = [False] * len(students)
            tasks.append((taskid,task,answer,tchr,taskdate,pic))
            allTasks.append((taskid, task, answer,tchr,taskdate,pic))
            lastClosed=False


            for std in students:
                bot.clear_step_handler_by_chat_id(chat_id=std)
                bot.send_message(std, msgg+'\n\n'+task)
                if ispic:
                    bot.send_photo(std,pic)
                bot.send_message(std, "Введите ответ на задание")

                bot.register_next_step_handler_by_chat_id(std, wait_answer)

            bot.send_message(message.chat.id,"Рассылка успешно завершена")
        else:
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
                  '\n', sys.exc_info())

def wait_answer(message):
    global task
    global f
    global taskdate
    global tchr
    global oldans
    global taskid
    try:
    # for k in range(1):
        if message.chat.id in students and \
                provcommands(message.text) and \
                not oldans and \
                not lastClosed:
            oldans=True
            std=students.index(message.chat.id)
            stdans=message.text
            stdname=std_names[std]
            uved = ''
            if otvetanet[std]:
                std_stat[std].pop(-1)
                stat_local[std].pop(-1)
                dbS.execute('DELETE FROM "{}" WHERE timeTask="{}"'.format(message.chat.id,taskdate))
                dbStats.commit()
            uved+= "Получен ответ на задание от ученика *"+stdname+'*\n'
            timeans=str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13]
            if stdans.lower()==answer.lower():
                isright=1
            else:
                isright=0
            std_stat[std].append((message.chat.id,taskid,timeans,taskdate,stdans,isright))
            stat_local[std].append((message.chat.id,taskid,timeans,taskdate,stdans,isright))

            dbS.execute('INSERT INTO "{}" VALUES("{}","{}","{}","{}","{}","{}")'.format(message.chat.id,
                                                                                        message.chat.id,
                                                                                        taskid,
                                                                                        timeans,
                                                                                        taskdate,
                                                                                        stdans,
                                                                                        isright))
            dbStats.commit()

            bot.send_message(message.chat.id, "Ваш ответ успешно принят.")
            userStat(tchr,message.chat.id,msg=uved)
            otvetanet[std]=False
            oldans=False
        elif lastClosed:
            bot.send_message(message.chat.id,"Задание закрыто преподавателем.")
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n', sys.exc_info())
    sendMenu(message.chat.id)



@bot.message_handler(commands=['stat'],content_types=['photo','text','sticker','file'])
def printstat(message):
    try:
    # for k in range(1):
        if message.chat.id in teacher:
            provcheck()
            stat(message.chat.id)
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
    sendMenu(message.chat.id)
@bot.message_handler(commands=['globalstat'],content_types=['photo','text','sticker','file'])
def printglobstat(message):
    try:
    # for k in range(1):
        if message.chat.id in teacher:

            provcheck()

            globstat(message.chat.id)
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())


@bot.message_handler(commands=['clearstat'],content_types=['photo','text','sticker','file'])
def clearstat(message):
    global taskcount
    try:
        if message.chat.id in teacher:
            for std in stat_local:
                std.clear()
            taskcount = 0
            bot.send_message(message.chat.id, "Статистика очищена")
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())

@bot.message_handler(commands=['sendstats'],content_types=['photo','text','sticker','file'])
def countsendstats(message):
    try:
        if message.chat.id in teacher:
            botmsg=bot.send_message(message.chat.id,
                             "За сколько последних заданий вы хотите разослать статистику? (Введите число) \nВведите 0, если хотите разослать всю статистику.",
                             reply_markup=cancel)
            previd=botmsg.message_id
            startCheckInactivity(message.chat.id)
            bot.register_next_step_handler_by_chat_id(message.chat.id, sendstats, *[previd])
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return

    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
def sendstats(message,previd):
    try:
        bot.edit_message_reply_markup(message.chat.id, previd)
        countoftasks = int(message.text)
        provcheck()
        finishCheckInactivity(message.chat.id)
        if len(tasks)==0:
            bot.send_message(message.chat.id, "Статистика пуста",
                             parse_mode="Markdown")
            sendMenu(message.chat.id)
            return
        for std in students:
            msg = 'Преподаватель *'+tchr_names[teacher.index(message.chat.id)]+'* выслал Вам статистику\n'
            userStat(std, std, countoftasks, msg)
        bot.send_message(message.chat.id,'Рассылка статистики успешно завершена')
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
    sendMenu(message.chat.id)

@bot.message_handler(commands=['addteacher'],content_types=['photo','text','sticker','file'])
def addtchr(message):
    try:
        if message.chat.id==owner:
            msg='Выберите пользователя, которого хотите сделать учителем:\n'
            for std in range(len(students)):
                name=std_names[std]
                msg+=str(std+1)+') '+name+' ('+str(students[std])+')\n'
            botmsg=bot.send_message(owner,msg,reply_markup=cancel)
            previd=botmsg.message_id
            startCheckInactivity(message.chat.id)
            bot.register_next_step_handler_by_chat_id(message.chat.id, tchrname,*[previd])
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())

def tchrname(message,previd):
    global insertdb
    try:
    # for i in range(1):
        finishCheckInactivity(message.chat.id)
        bot.edit_message_reply_markup(message.chat.id, previd)
        num = int(message.text)
        if students[num-1] in teacher:
            bot.send_message(owner,"Пользователь уже является учителем")
            return
        numv=students[num-1]
        dbU.execute("UPDATE users SET teacher = 1 WHERE id = (?)",(numv,))
        dbUsers.commit()
        teacher.append(students[num-1])
        teacher.sort()
        tchr_names.insert(teacher.index(students[num-1]),std_names[num-1])
        bot.send_message(students[num-1],"Вы были назначены учителем.")
        students.pop(num-1)
        std_names.pop(num-1)
        bot.send_message(owner, "Пользователь назначен учителем")
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())


@bot.message_handler(commands=['removeteacher'],content_types=['photo','text','sticker','file'])
def removeteacher(message):  # СТАРТ
    try:
        if message.chat.id==owner:
            msg = 'Выберите пользователя, которого хотите понизить:\n'
            for std in range(len(teacher)):
                name = tchr_names[std]
                msg += str(std + 1) + ') ' + name + ' (' + str(teacher[std]) + ')\n'
            botmsg=bot.send_message(owner, msg,reply_markup=cancel)
            previd=botmsg.message_id
            startCheckInactivity(message.chat.id)
            bot.register_next_step_handler_by_chat_id(message.chat.id, tchrnamer,*[previd])
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
def tchrnamer(message,previd):
    try:
    # for k in range (1):
        finishCheckInactivity(message.chat.id)
        bot.edit_message_reply_markup(message.chat.id, previd)
        num = int(message.text)-1
        dbU.execute("UPDATE users SET teacher = 0 WHERE id = (?)", (teacher[num],))
        dbUsers.commit()
        students.append(teacher[num])
        students.sort()
        updusers()
        std_names.insert(students.index(teacher[num]),tchr_names[num])
        bot.send_message(teacher[num], "Вы были сняты с поста учителя.")
        teacher.pop(num)
        tchr_names.pop(num)
        bot.send_message(owner, "Учитель успешно удален")
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())

@bot.message_handler(commands=['removestudent'], content_types=['photo', 'text', 'sticker', 'file'])
def removestudent(message):  # СТАРТ
    try:
    # for k in
        if message.chat.id == owner or message.chat.id in teacher:
            msg = '*Выберите пользователя, которого хотите удалить:*\n\n'
            for std in range(len(students)):
                name = std_names[std]
                msg += str(std + 1) + ') ' + name + ' _(' + str(students[std]) + ')_\n'
            botmsg=bot.send_message(message.chat.id, msg,reply_markup=cancel,parse_mode='markdown')
            previd=botmsg.message_id
            startCheckInactivity(message.chat.id)
            bot.register_next_step_handler_by_chat_id(message.chat.id, stdnamer,*[previd])
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())

def stdnamer(message,previd):
    try:
    # for l in range(1):
        bot.edit_message_reply_markup(message.chat.id, previd)
        finishCheckInactivity(message.chat.id)
        num = int(message.text) - 1
        if num>len(students):
            bot.send_message(message.chat.id, 'Указанного пользователя не существует. Попробуйте еще раз')
            bot.register_next_step_handler_by_chat_id(message.chat.id, stdnamer,reply_markup=cancel)
        if students[num]==owner:
            bot.send_message(message.chat.id, 'Вы не можете забанить создателя.')
            msg="Вас пытался забанить "+tchr_names[teacher.index(message.chat.id)]+" ("+str(message.chat.id)+")."
            bot.send_message(owner,msg)
            return
        provcheck()

        userGlobalStat(message.chat.id, students[num], 0, clearing=True)
        dbU.execute("DELETE FROM users WHERE id = (?)", (students[num],))
        dbUsers.commit()
        # Если нужно удалять стату из бд
        # dbS.execute('DROP TABLE "{}"'.format(students[num]))

        stat_local.pop(num)
        std_stat.pop(num)
        std_names.pop(num)
        students.pop(num)
        updusers()


        bot.send_message(message.chat.id, text="Пользователь успешно удален")
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n', sys.exc_info())
    sendMenu(message.chat.id)

@bot.message_handler(commands=['clearglobalstat'], content_types=['photo', 'text', 'sticker', 'file'])
def clearglobalstat(message):
    try:
        if message.chat.id==owner:
            botmsg=bot.send_message(owner,"Вы уверены?",reply_markup=cancel)
            previd=botmsg.message_id
            startCheckInactivity(message.chat.id)
            bot.register_next_step_handler_by_chat_id(owner, confirmclearstat,*[previd])
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
def confirmclearstat(message,previd):
    global taskcount
    try:
    # for k in range(1):
        finishCheckInactivity(message.chat.id)
        bot.edit_message_reply_markup(message.chat.id, previd)
        if message.text.lower()=="да":
            globstat(owner,True)
            for std in students:
                dbS.execute('DELETE FROM "{}" WHERE userID="{}"'.format(std,std))
            dbStats.commit()
            dbT.execute('DELETE FROM allTasks')
            dbTasks.commit()
            for std in stat_local:
                std.clear()
            taskcount = 0
            bot.send_message(owner,"Вся статистика успешно очищена")
        else:
            bot.send_message(owner, "Очистка всей статистики отменена")
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
                  '\n', sys.exc_info())

@bot.message_handler(commands=['renamestudent'], content_types=['photo', 'text', 'sticker', 'file'])
def renamestd(message):
    try:
        if message.chat.id==owner or message.chat.id in teacher:
            msg = '*Выберите пользователя, которого хотите переименовать:*\n\n'
            for std in range(len(students)):
                name = std_names[std]
                msg += str(std + 1) + ') ' + name + ' _(' + str(students[std]) + ')_\n'
            botmsg=bot.send_message(message.chat.id, msg,reply_markup=cancel,parse_mode='markdown')
            previd=botmsg.message_id
            startCheckInactivity(message.chat.id)
            bot.register_next_step_handler_by_chat_id(message.chat.id, stdrename,*[previd])
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
def stdrename(message,previd):
    global numofrenamingstd
    try:
    # for l in range(1):
        startCheckInactivity(message.chat.id)
        bot.edit_message_reply_markup(message.chat.id, previd)
        numofrenamingstd = int(message.text) - 1
        botmsg=bot.send_message(message.chat.id,"Введите новое имя",reply_markup=cancel)
        previd=botmsg.message_id
        bot.register_next_step_handler_by_chat_id(message.chat.id, newname,*[previd])
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
def newname(message,previd):
    global numofrenamingstd
    try:
    # for l in range(1):
        finishCheckInactivity(message.chat.id)
        bot.edit_message_reply_markup(message.chat.id, previd)
        newstdname=message.text
        if students[numofrenamingstd] == owner:
            bot.send_message(message.chat.id, 'Вы не можете переименовать создателя.')
            msg = "Вас пытался переименовать " + tchr_names[teacher.index(message.chat.id)] + " (" + str(
                message.chat.id) + ") в "+newstdname
            bot.send_message(owner, msg)
            return
        dbU.execute("UPDATE users SET name = (?) WHERE id = (?)", (newstdname,students[numofrenamingstd],))
        dbUsers.commit()
        std_names[numofrenamingstd]=newstdname
        bot.send_message(message.chat.id,"Пользователь успешно переименован")
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
    sendMenu(message.chat.id)

@bot.message_handler(commands=['renameteacher'], content_types=['photo', 'text', 'sticker', 'file'])
def renametchr(message):
    try:
        if message.chat.id==owner:
            msg = 'Выберите учителя, которого хотите переименовать:\n'
            for std in range(len(teacher)):
                name = tchr_names[std]
                msg += str(std + 1) + ') ' + name + ' (' + str(teacher[std]) + ')\n'
            botmsg=bot.send_message(owner, msg,reply_markup=cancel)
            previd=botmsg.message_id
            startCheckInactivity(message.chat.id)
            bot.register_next_step_handler_by_chat_id(owner, tchrrename,*[previd])
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
def tchrrename(message,previd):
    global numofrenamingtchr
    try:
    # for l in range(1):
        startCheckInactivity(message.chat.id)
        bot.edit_message_reply_markup(message.chat.id, previd)
        numofrenamingtchr = int(message.text) - 1
        botmsg=bot.send_message(message.chat.id,"Введите новое имя",reply_markup=cancel)
        previd = botmsg.message_id
        bot.register_next_step_handler_by_chat_id(owner, newnametchr,*[previd])
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
def newnametchr(message,previd):
    global numofrenamingtchr
    try:
        # for l in range(1):
        finishCheckInactivity(message.chat.id)
        bot.edit_message_reply_markup(message.chat.id, previd)
        newtchrname=message.text
        dbU.execute("UPDATE users SET name = (?) WHERE id = (?)", (newtchrname, teacher[numofrenamingtchr],))
        dbUsers.commit()
        tchr_names[numofrenamingtchr]=newtchrname
        bot.send_message(message.chat.id,"Учитель успешно переименован")
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())

@bot.message_handler(commands=['users'], content_types=['photo', 'text', 'sticker', 'file'])
def printlistofusers(message):
    try:
    # for k in range(1):
        if message.chat.id==owner:
            msg='*Владелец*\n'
            msg+=str(owner)+'\n\n'
            msg+='*Учителя*\n'
            for std in range(len(teacher)):
                name = tchr_names[std]
                msg += str(std + 1) + ') ' + name + ' (' + str(teacher[std]) + ')\n'
            msg+='\n*Ученики*\n'
            for std in range(len(students)):
                name = std_names[std]
                msg += str(std + 1) + ') ' + name + ' (' + str(students[std]) + ')\n'
            bot.send_message(owner,msg,parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())


@bot.message_handler(commands=['userstat'], content_types=['photo', 'text', 'sticker', 'file'])
def listuserstat(message):
    try:
    # for k in range(1):
        if message.chat.id in teacher and message.chat.id!=owner:
            msg = 'Выберите пользователя, статистику которого хотите посмотреть:\n'
            for std in range(len(students)):
                name = std_names[std]
                msg += str(std + 1) + ') ' + name + ' (' + str(students[std]) + ')\n'
            botmsg=bot.send_message(message.chat.id, msg,reply_markup=cancel)
            previd = botmsg.message_id
            startCheckInactivity(message.chat.id)
            bot.register_next_step_handler_by_chat_id(message.chat.id, countuserstat,*[previd])
        elif message.chat.id==owner:
            msg = 'Выберите пользователя, статистику которого хотите посмотреть:\n'
            lastn=len(students)-1

            for std in range(len(students)):
                name = std_names[std]
                msg += str(std + 1) + ') ' + name + ' (' + str(students[std]) + ')\n'

            for std in range(len(teacher)):
                name = tchr_names[std]
                msg += str(std + 2 + lastn) + ') ' + name + ' (' + str(teacher[std]) + ')\n'

            botmsg=bot.send_message(message.chat.id, msg,reply_markup=cancel)
            previd = botmsg.message_id
            startCheckInactivity(message.chat.id)
            bot.register_next_step_handler_by_chat_id(message.chat.id, countuserstat,*[previd])
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
                  '\n', sys.exc_info())
def countuserstat(message,previd):
    global numofuserstat
    try:
    # for l in range(1):
        startCheckInactivity(message.chat.id)
        bot.edit_message_reply_markup(message.chat.id, previd)
        if message.chat.id==owner:
            numofuserstat = int(message.text) - 1
            if numofuserstat>len(students)-1:
                numofuserstat-=(len(students)-1)
        else:
            numofuserstat = int(message.text) - 1
        botmsg=bot.send_message(message.chat.id,
                         "За сколько последних заданий вы хотите увидеть статистику? (Введите число) \nВведите 0, если хотите увидеть всю статистику пользователя.",
                         reply_markup=cancel)
        previd = botmsg.message_id
        bot.register_next_step_handler_by_chat_id(message.chat.id, printuserstat,*[previd])
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())

def printuserstat(message,previd):
    global numofuserstat
    global countoftasks
    try:
        finishCheckInactivity(message.chat.id)
        bot.edit_message_reply_markup(message.chat.id, previd)
        countoftasks = int(message.text)
        msg='Статистика пользователя *'+std_names[numofuserstat]+'*\n'
        userStat(message.chat.id,students[numofuserstat],countoftasks,msg)

    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
    sendMenu(message.chat.id)

@bot.message_handler(commands=['mystat'], content_types=['photo', 'text', 'sticker', 'file'])

def countmystat(message):
    try:
        startCheckInactivity(message.chat.id)
        botmsg=bot.send_message(message.chat.id,
                         "За сколько последних заданий вы хотите увидеть статистику? (Введите число) \nВведите 0, если хотите увидеть всю статистику.",
                         reply_markup=cancel)
        previd = botmsg.message_id
        bot.register_next_step_handler_by_chat_id(message.chat.id, printmystat,*[previd])
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
def printmystat(message,previd):
    global countoftasks
    try:
        finishCheckInactivity(message.chat.id)
        bot.edit_message_reply_markup(message.chat.id, previd)
        countoftasks = int(message.text)
        msg='Статистика пользователя *'+std_names[numofuserstat]+'*\n'
        userStat(message.chat.id,message.chat.id,countoftasks,msg)

    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
    sendMenu(message.chat.id)

@bot.message_handler(commands=['userglobalstat'], content_types=['photo', 'text', 'sticker', 'file'])
def listuserglobalstat(message):
    try:
        if message.chat.id==owner:
            msg = 'Выберите пользователя, статистику которого хотите посмотреть:\n'
            lastn=len(students)-1

            for std in range(len(students)):
                name = std_names[std]
                msg += str(std + 1) + ') ' + name + ' (' + str(students[std]) + ')\n'

            for std in range(len(teacher)):
                name = tchr_names[std]
                msg += str(std + 2 + lastn) + ') ' + name + ' (' + str(teacher[std]) + ')\n'

            botmsg=bot.send_message(message.chat.id, msg,reply_markup=cancel)
            previd = botmsg.message_id
            startCheckInactivity(message.chat.id)
            bot.register_next_step_handler_by_chat_id(message.chat.id, countuserglobalstat,*[previd])
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
def countuserglobalstat(message,previd):
    global numofuserstat
    try:
        startCheckInactivity(message.chat.id)
        bot.edit_message_reply_markup(message.chat.id, previd)
        if message.chat.id==owner:
            numofuserstat = int(message.text) - 1
            if numofuserstat>len(students)-1:
                numofuserstat-=(len(students)-1)
        else:
            numofuserstat = int(message.text) - 1
        botmsg=bot.send_message(message.chat.id,
                         "За сколько последних заданий вы хотите увидеть статистику? (Введите число) \nВведите 0, если хотите увидеть всю статистику пользователя.",
                         reply_markup=cancel)
        previd = botmsg.message_id
        bot.register_next_step_handler_by_chat_id(message.chat.id, printuserglobalstat,*[previd])
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
def printuserglobalstat(message,previd):
    global numofuserstat
    global countoftasks
    try:
    # for l in range(1):
        bot.edit_message_reply_markup(message.chat.id, previd)
        countoftasks = int(message.text)
        finishCheckInactivity(message.chat.id)
        try:
            msg='Статистика пользователя *'+std_names[numofuserstat]+'*\n'
            userGlobalStat(message.chat.id, students[numofuserstat], countoftasks, msg)
        except:
            numofuserstat-=len(students)
            msg = 'Статистика пользователя *' + tchr_names[numofuserstat] + '*\n'
            userGlobalStat(message.chat.id, teacher[numofuserstat], countoftasks, msg)


    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n',sys.exc_info())
@bot.message_handler(commands=['tasklog'], content_types=['photo', 'text', 'sticker', 'file'])
def printtasklog(message):
    try:
        if message.chat.id==owner:
            dbT.execute('SELECT * FROM allTasks')
            mes=str(dbT.fetchall())
            taskwrite = open('TaskLog.txt', 'w')
            taskwrite.write(mes)
            taskwrite.close()
            bot.send_message(owner,
                             "Статистика отправки заданий будет отправлена в формате .txt")
            bot.send_document(owner, open('TaskLog.txt'))
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n', sys.exc_info())

@bot.message_handler(commands=['closetask'], content_types=['photo', 'text', 'sticker', 'file'])
def closelasttask(message):
    global lastClosed
    try:
        if message.chat.id in teacher:
            lastClosed=True
            bot.send_message(message.chat.id,"Задание успешно закрыто.")
            provcheck()
            stat(message.chat.id,count=1)
            for std in students:
                bot.send_message(std,"Последнее задание закрыто учителем. Вы можете посмотреть результат с помощью команды /mystat")
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Произошла ошибка! Напишите @TeaJdun")
        print(str(datetime.datetime.now(pytz.timezone('Europe/Moscow')))[:-13],
              '\n', sys.exc_info())
@bot.message_handler(commands=['taskslist'], content_types=['photo', 'text', 'sticker', 'file'])
def printtaskslist(message):
    if message.chat.id in teacher or message.chat.id==owner:
        sendSite(message.chat.id,
                 'taskslist',
                 'База Данных заданий',
                 'Вы можете посмотреть базу данных заданий, перейдя по ссылке ниже',
                 True)
        return
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
        return
@bot.message_handler(commands=['info','help'], content_types=['photo', 'text', 'sticker', 'file'])
def info(message):
    msg='*ИНФОРМАЦИЯ*\n\n'
    msg+='*Ваша роль:    *'
    if message.chat.id in teacher:
        msg+='Преподаватель'
    else:
        msg+='Ученик'
    msg+='\n'
    msg+='*Ваше имя:    *'
    if message.chat.id in teacher:
        msg+=tchr_names[uid(message.chat.id)]
    else:
        msg += std_names[uid(message.chat.id)]
    msg+='\n\n*Доступные команды:*\n'
    if message.chat.id in teacher:
        msg+='''
        /addtask - _Отправка/Запись в базу данных задания_
        /closetask - _Закрыть возможность ответа на задание._
        /tasklist - _Просмотр базы данных заданий_
        /stat - _Просмотр статистики_
        /clearstat - _Очистка статистики_
        /userstat - _Посмотреть статистику конкретного ученика_
        /sendstats - _Выслать ученикам их статистику_
        /renamestudent - _Переименовать ученика_
        /rename - _Изменить своё имя_
        
        '''
    else:
        msg+='''/mystat - _Посмотреть свою стастику_
        /rename - _Изменить своё имя_
        '''
    bot.send_message(message.chat.id,msg,parse_mode='Markdown')
@bot.message_handler(commands=['rename'], content_types=['photo', 'text', 'sticker', 'file'])
def renamemyself(message):
    bot.send_message(message.chat.id,'Введите новое имя')
    bot.register_next_step_handler_by_chat_id(message.chat.id,newnamemyself)
def newnamemyself(message):
    nn=message.text
    if message.chat.id in teacher:
        tchr_names[uid(message.chat.id)]=nn
    dbU.execute("UPDATE users SET name = (?) WHERE id = (?)", (nn, message.chat.id,))
    dbUsers.commit()
    updusers()
    bot.send_message(message.chat.id, 'Вы были успешно переименованы')

@bot.message_handler(commands=['menu'], content_types=['photo', 'text', 'sticker', 'file'])
def sendMenuCommand(message):
    sendMenu(message.chat.id)


# ======================================================================================================================


print(ssh_tunnel)
print(ssh_tunnel.public_url+'/taskslist')
print(ssh_tunnel.public_url+'/localstat')
app = Flask(__name__)
@app.route('/')
def startmsg():
    return 'Приветствую на сайте!'

@app.route('/auth')
def authID():
    return render_template("auth.html")
@app.route('/taskslist')
def taskListSite():
    global urlcc
    global urlpc
    dbT.execute("select * from tasks")
    rows = dbT.fetchall()
    docs = googledocs()
    for row in range(len(rows)):
        rows[row]=list(rows[row])
        if rows[row][3]!=None:
            filetk=str(filetoken(rows[row][3],docs))
            rows[row][3]="https://drive.google.com/uc?export=view&id="+filetk
    return render_template("tasks.html", rows=rows)

@app.route('/localstat')
def localStatSite():
    stds=[[]]*len(Students)
    provcheck()
    for std in range(len(stat_local)):
        try:
            if stat_local[std][0][0] in teacher:
                continue
        except:
            break
        for task in stat_local[std]:
            row=[std_names[uid(task[0])],
                 task[1],
                 task[2],
                 task[3],
                 task[4]]
            if task[5]==1:
                row.append('Верно')
            else:
                row.append('Неверно')
            stds[std].append(row)
    return render_template("usersstat.html", users=stds)
docs=''
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
gauth = GoogleAuth()
gauth.LoadCredentialsFile("mycreds.txt")
if gauth.credentials is None:
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:

    gauth.Refresh()
else:

    gauth.Authorize()

gauth.SaveCredentialsFile("mycreds.txt")
drive = GoogleDrive(gauth)

def uploadfile(file_id):
    global folder
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    src = 'temp/' + file_id + '.jpg'
    with open(src, 'wb') as new_file:
        new_file.write(downloaded_file)
    file2 = drive.CreateFile({'parents': [{'id': folder}]})
    file2.SetContentFile(src)
    file2.Upload()

def filetoken(name,docs):
    for doc in docs:
        if name in doc['title']:
            return doc['id']
def googledocs():
    global folder
    file_list = drive.ListFile({'q': "{} in parents and trashed=false".format(folder)}).GetList()
    return file_list

@bot.message_handler(commands=['startbot'],content_types=['photo','text','sticker','file'])
def flaskStart():
    global app
    app.run(host="0.0.0.0",
            port=302)

print("Bot!")
bot.polling(none_stop=True, interval=0)




