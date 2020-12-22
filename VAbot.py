import telebot
import datetime



def uniq(a):
    b=[]
    for k in a:
        if k not in b:
            b.append(k)
    return b


bot = telebot.TeleBot('1410579467:AAGztbHNDNMDnPpGfJ7gZI4-bY1cWxy3wRA')
markdown = """
    *bold text*
    _italic text_
    [text](URL)
    """
#452479885 - Олег
#837523559 - Маша
owner=947202095
teacher=[113547028,947202095]
students=[452479885,947202095]
std_names=["Леоненко Олег","Щагин Дмитрий"]
std_stat=[[],[]]
tasks=[]
b=''
task=''; answer='';wait_right_answer=False; taskcount=0; taskdate=""
pic=''
ispic=False

def stat(id):
    mes=""
    for student in std_stat:
        for k in range(len(student) // 6):
            mes += "*" + str(student[0 + k * 6]) + '* \n'
            mes += "*Задание:*    " + str(student[1 + k * 6]) + ' \n'
            mes += "*Время сдачи:*    " + str(student[2 + k * 6]) + ' \n'
            mes += "*Ответ совпал?*    " + str(student[3 + k * 6]) + ' \n'
            mes += "*Ответ пользователя:*    " + str(student[4 + k * 6]) + ' \n'
            mes += "*Правильный ответ:*    " + str(student[5 + k * 6]) + ' \n\n'
        mes += '\n\n'

    bot.send_message(id, mes, parse_mode="Markdown")

def provcheck():
    global taskcount
    for std in range(len(std_stat)):
        if len(std_stat[std]) // 6 < taskcount:
            stdname = std_names[std]
            std_stat[std].append(stdname)
            # std_stat[std].append(tasks[-1])
            std_stat[std].append(taskdate)
            std_stat[std].append("_Ответа нет_")
            std_stat[std].append("_Ответа нет_")
            std_stat[std].append("_Ответа нет_")
            std_stat[std].append(answer)
        if len(std_stat[std]) // 6 > taskcount:
            for j in range(len(std_stat[std]) - taskcount * 6):
                std_stat[std].pop(-1)


@bot.message_handler(commands=['start'],content_types=['photo','text','sticker','file'])
def start_message(message):  # СТАРТ
    global f
    try:
        if message.chat.id in students or message.chat.id in teacher :
            bot.send_message(message.chat.id, text="Вы уже зарегистрированы")
            return
        students.append(message.chat.id)
        bot.send_message(message.chat.id, text="Введите, пожалуйста, свою фамилию и имя")
        bot.register_next_step_handler_by_chat_id(message.chat.id, FI)
    except:
        bot.send_message(message.chat.id, text="Пройзошла ошибка! Напишите @TeaJdun")
def FI(message):
    try:
        fi=str(message.text)
        std_names.append(fi)
        std_stat.append([])
        print(std_names[-1],students[-1])
    except:
        bot.send_message(message.chat.id, text="Пройзошла ошибка! Напишите @TeaJdun")


@bot.message_handler(commands=['send'],content_types=['photo','text','sticker','file'])
def send_task(message):
    global task
    global wait_right_answer
    global taskcount
    try:
        if message.chat.id==owner or message.chat.id in teacher:
            tchr = message.chat.id
            provcheck()
            task=message.text[6:]
            k1 = telebot.types.ReplyKeyboardMarkup(True,True)
            k1.row('Да', 'Нет')
            bot.send_message(tchr, "Желаете прикрепить картинку?",reply_markup=k1)
            bot.register_next_step_handler_by_chat_id(tchr,add_pic)
        else:
            bot.send_message(message.chat.id,"У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Пройзошла ошибка! Напишите @TeaJdun")
def add_pic(message):
    try:
        if message.text=='Да':
            bot.send_message(message.chat.id, "Пришлите мне картинку")
            bot.register_next_step_handler_by_chat_id(message.chat.id, send_pic)
        else:
            bot.send_message(message.chat.id, "Введите правильный ответ на задание")
            bot.register_next_step_handler_by_chat_id(message.chat.id, right_answer)
    except:
        bot.send_message(message.chat.id, text="Пройзошла ошибка! Напишите @TeaJdun")
def send_pic(message):
    try:
        global pic
        global ispic
        ispic=True
        pic=message.photo[0].file_id
        bot.send_message(message.chat.id, "Введите правильный ответ на задание")
        bot.register_next_step_handler_by_chat_id(message.chat.id, right_answer)
    except:
        bot.send_message(message.chat.id, text="Пройзошла ошибка! Напишите @TeaJdun")

def right_answer(message):
    global answer
    global task
    global ispic
    global taskcount
    global taskdate
    try:
        if message.chat.id==owner or message.chat.id in teacher:
            answer=message.text
            print(answer)
            tasks.append(task)
            taskcount+=1
            taskdate=str(datetime.datetime.now())[:10]
            for std in students:
                bot.send_message(std, task)
                if ispic:
                    bot.send_photo(std,pic)
                bot.send_message(std, "Введите ответ на задание")

                bot.register_next_step_handler_by_chat_id(std, wait_answer)
            ispic=False
            bot.send_message(message.chat.id,"Рассылка успешно завершена")
        else:
            return
    except:
        bot.send_message(message.chat.id, text="Пройзошла ошибка! Напишите @TeaJdun")

def wait_answer(message):
    global task
    global f
    global taskdate
    try:
        if message.chat.id in students and "/start" not in message.text:
            std=students.index(message.chat.id)
            stdans=message.text
            stdname=std_names[std]
            std_stat[std].append(stdname)
            #std_stat[std].append(tasks[-1])
            std_stat[std].append(taskdate)
            std_stat[std].append(str(datetime.datetime.now())[:-7])
            std_stat[std].append(stdans.lower()==answer.lower())
            std_stat[std].append(stdans)
            std_stat[std].append(answer)
            print(std_stat)
        else:
            if "/send" in message.text:
                if message.chat.id == owner or message.chat.id in teacher:
                    tchr = message.chat.id
                    provcheck()
                    task = message.text[6:]
                    k1 = telebot.types.ReplyKeyboardMarkup(True, True)
                    k1.row('Да', 'Нет')
                    bot.send_message(tchr, "Желаете прикрепить картинку?", reply_markup=k1)
                    bot.register_next_step_handler_by_chat_id(tchr, add_pic)
                else:
                    bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
                    return
            elif "/stat" in message.text:
                if message.chat.id in teacher:
                    provcheck()
                    stat(message.chat.id)
                else:
                    bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
                    return
            elif "/start" in message.text:

                if message.chat.id in students:
                    bot.send_message(message.chat.id, text="Вы уже зарегистрированы")
                    return
                students.append(message.chat.id)
                bot.send_message(message.chat.id, text="Введите, пожалуйста, свою фамилию и имя")
                bot.register_next_step_handler_by_chat_id(message.chat.id, FI)
    except:
        bot.send_message(message.chat.id, text="Пройзошла ошибка! Напишите @TeaJdun")



@bot.message_handler(commands=['stat'],content_types=['photo','text','sticker','file'])
def prinstat(message):
    try:
        if message.chat.id in teacher:
            provcheck()
            stat(message.chat.id)
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Пройзошла ошибка! Напишите @TeaJdun")



@bot.message_handler(commands=['clearstat'],content_types=['photo','text','sticker','file'])
def clearstat(message):
    global taskcount
    try:
        if message.chat.id in teacher:
            for std in std_stat:
                std.clear()
            taskcount = 0
            bot.send_message(message.chat.id, "Статистика очищена")
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return
    except:
        bot.send_message(message.chat.id, text="Пройзошла ошибка! Напишите @TeaJdun")

@bot.message_handler(commands=['sendstats'],content_types=['photo','text','sticker','file'])
def sendstats(message):
    try:
        if message.chat.id in teacher:
            provcheck()
            ind=0
            for student in std_stat:
                mes = ""
                k=len(student)//6-1
                #mes += "*" + str(student[0 + k * 6]) + '* \n'
                mes += "*Задание:*    " + str(student[1 + k * 6]) + ' \n'
                mes += "*Время сдачи:*    " + str(student[2 + k * 6]) + ' \n'
                mes += "*Ответ совпал?*    " + str(student[3 + k * 6]) + ' \n'
                mes += "*Ответ пользователя:*    " + str(student[4 + k * 6]) + ' \n'
                mes += "*Правильный ответ:*    " + str(student[5 + k * 6]) + ' \n\n'
                bot.send_message(students[ind], mes, parse_mode="Markdown")
                ind+=1
            bot.send_message(message.chat.id, "Рассылка успешно завершена")
        else:
            bot.send_message(message.chat.id, "У вас нет доступа к этой команде")
            return

    except:
        bot.send_message(message.chat.id, text="Пройзошла ошибка! Напишите @TeaJdun")






bot.polling()