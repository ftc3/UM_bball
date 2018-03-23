import urllib2
from bs4 import BeautifulSoup
import re
import time
import csv


# valid years: 2005 - 2018
year = 2018
if year == 2018: year_code = 456
if year != 2018: year_code = year - 1976

varnames = []
file_list = []
row_index = 0
game_count = 0
errors = 0

#### html of schedule page ####
schedule_req = urllib2.Request('http://mgoblue.com/schedule.aspx?schedule=' + str(year_code), headers={ 'User-Agent': 'Mozilla/5.0' })
schedule = urllib2.urlopen(schedule_req).read()

### Optional saving html from schedule page, using saved data ###
# schedsave = open('schedule.txt', 'w')
# schedsave.write(str(schedule))
# schedule = open('schedule13.txt', 'r').read()

#### bs parse locating game container
sched_parse = BeautifulSoup(schedule, 'html.parser')
games = sched_parse.find('ul', {'class':"sidearm-schedule-games-container"}).findAll('li', {'class': 'sidearm-schedule-game'})
print len(games), 'games in the %s season' % year, '\n'

# ### investigating individual objects ####
# c = 0
# for g in games:
#     c +=1
#     print c, 'object', '\n', str(g)[0:200]
#     if c > 3: break

game_ids = []
for g in games:
    id = re.search('data-game-id=\"([0-9]+)\"', str(g))
    location = re.search(r'sidearm-schedule-(neutral|home|away)-game', str(g))
    game_tup = (id.group(1), location.group(1))
    game_ids.append(game_tup)
print len(game_ids), 'game ids: ', game_ids
time.sleep(10)

# Box scores page example
# http://mgoblue.com/boxscore.aspx?id=11503&path=mbball

#### html of a boxscore page ####
for game_id,location in game_ids:
    try:
        game_count +=1
        print '\n Getting data from game: ', game_count, 'of %s season' % year
        box_req = urllib2.Request('http://mgoblue.com/boxscore.aspx?id='+ game_id +'&path=mbball', headers={ 'User-Agent': 'Mozilla/5.0' })
        box = urllib2.urlopen(box_req).read()

        ### Optional saving html from boxscore, using saved data ###
        # box_save = open('box.txt', 'w')
        # box_save.write(str(box))
        # box = open('box.txt', 'r').read()

        box_parse = BeautifulSoup(box, 'html.parser')  # was just box
        team_score = box_parse.findAll('h2', {'class': 'sub-heading'})

        # finding whether Michigan is the away/home (0/1) team (position of Michigan's data)
        scoreboard = team_score[0].text + ' ' + team_score[1].text
        game_date = box_parse.find('dd').text
        print scoreboard, game_date

        if re.match(r'^Michigan\s[0-9]+$', str(team_score[0].text)):
            # away
            print 'away game'
            table_index = 0
        else:
            # home
            print 'home game'
            table_index = 1

        tables = box_parse.findAll('table', {'class':'sidearm-table overall-stats full hide-caption highlight-hover highlight-column-hover'})

        # away team is table[0], home team is table[1]
        rows = tables[table_index].findAll('tr')
        print len(rows)
        row_index = 0

        for row in rows:
            vals = row.findAll(['th', 'td'])
            final_row = []
            if row_index == 0:
                if game_count == 1:
                    for v in vals:
                        v2 = v.text
                        if re.match('(FG|3PT|FT)', v2):
                            metric = re.search('(FG|3PT|FT)', v2)
                            varnames.append(metric.group(0))
                            varnames.append(metric.group(0) + 'A')
                            continue
                        if re.match(r'ORB-DRB', v2):
                            rsearch = re.search(r'(ORB)-(DRB)', v2)
                            varnames.append(rsearch.group(1))
                            varnames.append(rsearch.group(2))
                            continue
                        if re.match(r'REB', v2): continue
                        varnames.append(v2)
                print len(varnames), varnames
                row_index +=1
                continue
            row_index += 1
            for v in vals:
                v2 = v.text
                # hyphenated numbers
                if re.match(r'[0-9]+-[0-9]+', v2):
                    rsearch = re.search(r'([0-9]+)-([0-9]+)', v2)
                    final_row.append(rsearch.group(1))
                    final_row.append(rsearch.group(2))
                    continue
                final_row.append(v2)
            rscore = re.search('\s([0-9]{2,3})\s.*\s([0-9]{2,3})$', scoreboard)
            rs = (int(rscore.group(1)), int(rscore.group(2)))
            regex_name = re.search('(.*)\s[0-9]{2,3}\s(.*)\s[0-9]{2,3}$', scoreboard)
            if table_index == 0:
                UM_score = rs[0]
                opp_score = rs[1]
                opp_name = regex_name.group(2)
            if table_index == 1:
                UM_score = rs[1]
                opp_score = rs[0]
                opp_name = regex_name.group(1)
            final_row.append(opp_name)
            final_row.append(opp_score)
            final_row.append(UM_score)
            final_row.append(game_date)
            final_row.append(location)
            if rs[0] > rs[1]:
                if table_index ==0 : final_row.append('W')
                if table_index ==1 : final_row.append('L')
            if rs[0] < rs[1]:
                if table_index ==1 : final_row.append('W')
                if table_index ==0 : final_row.append('L')
            f_row = []
            f_row.extend(final_row[:12])
            f_row.extend(final_row[13:])
            print len(f_row), f_row
            file_list.append(f_row)
        time.sleep(8)
    except:
        print 'ERROR FOR GAME ID: ', game_id
        errors += 1
        time.sleep(10)
        continue

varnames.extend(['Opponent', 'Opp_score', 'UM_score', 'Date', 'Court', 'Result'])
print len(varnames), varnames
print 'Number of errors :', errors

with open('UM_bball_%s.csv' % year, 'w') as out:
    csv_out = csv.writer(out)
    csv_out.writerow(varnames)
    for row in file_list:
        csv_out.writerow(row)
