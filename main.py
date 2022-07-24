from curses import wrapper
from curses.textpad import Textbox, rectangle
from dataclasses import dataclass, asdict
import dacite
import datetime
import json
import curses
import os
import sys
import time



@dataclass
class Config:
    test: str

@dataclass 
class Project:
    start: int
    end: int
    unit: str
    progress: float
    maxunit: float
    desc: str
    milestones: list[tuple[float, str]]
    priority: float



def init_main():
    conf = Config("foo")
    projects = []
    return Mainclass(conf, projects)


@dataclass
class Mainclass:
    config: Config
    projects: list[Project]

try:
    with open('db.json') as f:
        for line in f:
            loaded_dict = json.loads(line)
    mainclass = dacite.from_dict(data_class=Mainclass, data=loaded_dict)
    print("maybe no exception!")

except Exception as e:
    print("exception!!!", e)
    mainclass = init_main()


def save_db(mainclass):
    with open('db.json', 'w') as fp:
        json.dump(asdict(mainclass), fp)



def get_input(screen, prompt):
    screen.clear()
    screen.refresh()
    y, x = 0, 0
    screen.move(y, x)
    screen.addstr(prompt)
    y += 1 
    screen.move(y, x)
    desc = []
    maxlen = 999
    while (keypressed := screen.getkey()) != "\n":
        if keypressed in ('KEY_BACKSPACE', '\b', '\x7f'):
            if desc:
                desc.pop()
                y, x = screen.getyx()
                if not x and y:
                    x = maxlen
                screen.move(y, x - 1)
                screen.addstr(" ")
                screen.move(y, x - 1)
            continue
        if keypressed == "KEY_END":
            return None
        elif len(keypressed) > 1:
            continue
        else: # keypressed.isalnum() or keypressed == " ":
            desc.append(keypressed)
            try:
                screen.addstr(keypressed)
            except:
                y += 1
                maxlen = x
                x = 0
    screen.clear()
    return "".join(desc)
    



def new_project(screen, mainclass):
    start = int(time.time())
    while True:
        try:
            days = int(get_input(screen, "How many days?"))
            break
        except:
            screen.clear()
            screen.addstr("invalid input")
            screen.refresh()
            screen.getkey()

    end = start + days * 86400
    desc = get_input(screen, "description of project")
    unit = get_input(screen, "Name of unit (plural)")
    maxunit = float(get_input(screen, "how many " + unit +" are you supposed to do?"))
    progress = 0.0
    milestones = []
    newproject = Project(start, end, unit, progress, maxunit, desc, milestones, 0)
    mainclass.projects.append(newproject)




def calculate_priority(mainclass):
    for project in mainclass.projects:
        progress = project.progress / project.maxunit

        start = project.start 
        end   = project.end 
        now   = int(time.time())

        total_length  = end - start
        time_passed   = now - start
        elapsed_time  = time_passed / total_length

        ratio_time_left = 1 - elapsed_time
        progress_left   = 1 - progress
        priority =  progress_left / ratio_time_left

        sign = 1
        if priority > 1:
            priority **= -1
            sign = -1

        priority = 0.5 + sign * (1 - priority) / 2
        project.priority = round(priority*10, 1) 


def progbar(project):
    chars = 50 

    start = project.start 
    end   = project.end 
    now   = int(time.time())

    total_length  = end - start
    time_passed   = now - start

    elapsed_time  = round((time_passed / total_length) * chars)
    progress = round((project.progress / project.maxunit) * chars)

    bar = ""

    if progress < elapsed_time:
        bar += "#" * progress 
        bar += "-" * (elapsed_time - progress)
        bar += "~" * (chars - elapsed_time)
    else:
        bar += "#" * elapsed_time
        bar += "*" * (progress - elapsed_time) 
        bar += "~" * (chars - progress)


    return bar



def boxproject(stdscr, mainclass):
    prompts = [
            "description",
            "deadline (day, month, year)",
            ]
    vals = []
    for prompt in prompts:
        vals.append(user_input(stdscr, prompt))
    description = vals[0]
    deadline    = get_date_obj(vals[1])
    newproject  = Project(
            start = str(datetime.datetime.now().date()),
            end   = deadline,
            progress   = 0,
            desc  = description,
            milestones = [],
            priority = 1,
            )

    mainclass.projects.append(newproject)



def user_input(screen, prompt):
    screen.clear()
    screen.move(0,0)
    screen.addstr(prompt)
    screen.move(1, 0)
    entered = []

    while (keypressed := screen.getkey()) != "\n":

        if keypressed in ('KEY_BACKSPACE', '\b', '\x7f') and entered:
            y, x = screen.getyx()
            screen.move(1, x-1)
            screen.addstr(" ")
            screen.move(1, x-1)
            entered.pop()
        elif keypressed.isalnum() or keypressed == " ":
            screen.addstr(keypressed)
            entered.append(keypressed)
    return "".join(entered)

def print_help(screen):
    screen.clear()
    screen.move(0,0)
    screen.addstr("a: new project\n")
    screen.addstr("p: update progress\n")
    screen.addstr("e: edit description\n")
    screen.addstr("del: delete project\n")
    screen.addstr("q: quit")
    screen.refresh()
    curses.curs_set(0)
    screen.getkey()





def main(stdscr):
    selected_row = 0
    maxindex = len(mainclass.projects) - 1
    while True:
        calculate_priority(mainclass)
        mainclass.projects.sort(reverse=False, key=lambda x: x.priority)
        stdscr.clear()
        proqty = len(mainclass.projects)
        stdscr.move(0,0)
        stdscr.addstr("List of projects")
        for i, pro in enumerate(mainclass.projects):
            attr = 1
            if i == selected_row:
                attr |= curses.A_BOLD
            stdscr.move(i*2 + 1, 0)
            stdscr.addstr(f"{pro.desc}\t{round(pro.progress)} of {round(pro.maxunit)} {pro.unit}\t{pro.priority}", attr)
            stdscr.move(i*2 +2, 0)
            stdscr.addstr(progbar(pro))

        stdscr.addstr("\n\nPress ? for help")
        curses.curs_set(0)
        stdscr.refresh()
        
        match stdscr.getkey():
            case "?":
                print_help(stdscr) 
            case "a":
                new_project(stdscr, mainclass)
                maxindex += 1
            case "KEY_UP":
                if selected_row != 0:
                    selected_row -= 1
            case "KEY_DOWN":
                if selected_row != maxindex:
                    selected_row += 1
            case "KEY_DC":
                del mainclass.projects[selected_row]
            case "p":
                if (pri := user_input(stdscr, "update progress: ")).isnumeric():
                    mainclass.projects[selected_row].progress = float(pri)
            case "e":
                desc = user_input(stdscr, "Description: ")
                if desc:
                    mainclass.projects[selected_row].desc = desc 
            case "q":
                sys.exit()
        save_db(mainclass)
        stdscr.move(proqty, 0)

def envargs(args):
    for arg in args:
        match arg:
            case "update":
                calculate_priority(mainclass)
                save_db(mainclass)
                sys.exit(0)
            case _:
                continue




envargs(sys.argv)


wrapper(main)

















