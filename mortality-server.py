# A simple server for mortality data
#
# Requires the bottle framework
# (sufficient to have bottle.py in the same folder)
#
# run with:
#
#    python mortality-server 8080
#
# You can use any legal port number instead of 8080
# of course

from bottle import get, run, request, static_file
import sys
import sqlite3


# the name of the database file
MORTALITYDB = "mortality.db"


# Function to take a list of rows (each a dictionary)
# and group them by the value of a field F
# creating a dictionary with a key for each value
# in F mapping to the rows with that value for field F 

def group_by (rows,field):
    values = set([r[field] for r in rows])
    grouped_rows = {}
    for (value,rows) in [(value,[r for r in rows if r[field]==value]) for value in values]:
        grouped_rows[value] = rows
    return grouped_rows


# Pulls the data from the database file
# All rows with the given gender
# (all rows if gender is None)
# Group the results by cause of death and
# by year

def pullVizData():
 # return year, race recode 5, education, place of death/ activity, manner, # 
    conn = sqlite3.connect(MORTALITYDB)
    cur = conn.cursor()

    avgAgeData = {}
    try:
        # cur.execute("""SELECT mortality.year, 
        #                     mortality.Education,
        #                     mortality.Race_Recode_5, 
        #                     mortality.Place_Of_Death,
        #                     mortality.Activity_Code,
        #                     mortality.Manner_Of_Death, 
        #                     COUNT(mortality.year)
        #                 FROM mortality 
        #                 WHERE mortality.Education != '99' AND 
        #                     mortality.Education != '9' AND 
        #                     mortality.Education != '' AND 
        #                     mortality.Place_Of_Death != '9' AND
        #                     mortality.Activity_Code != '' AND
        #                     mortality.Manner_Of_Death !=''  
        #                 GROUP BY mortality.year, 
        #                     mortality.Education,
        #                     mortality.Race_Recode_5, 
        #                     mortality.Place_Of_Death,
        #                     mortality.Activity_Code,
        #                     mortality.Manner_Of_Death """)
        cur.execute("""SELECT mortality.year, 
                            mortality.Education,
                            mortality.Race_Recode_5, 
                            mortality.Place_Of_Death,
                            mortality.Activity_Code,
                            mortality.Manner_Of_Death, 
                            COUNT(mortality.year)
                        FROM mortality 
                        GROUP BY mortality.year, 
                            mortality.Education,
                            mortality.Race_Recode_5, 
                            mortality.Place_Of_Death,
                            mortality.Activity_Code,
                            mortality.Manner_Of_Death """)


        data = [{"year": int(year),
            "education": education,
            "race": race,
            "place": place,
            "activity": activity,
            "manner": manner,
            "count":count} for (year, education, race, place, activity, manner, count) in cur.fetchall()]

        print data 
        #groupedData = group_by(data, "year")
        #jsonData = []

        return data;
        
    except:
        print "ERROR!!!"
        conn.close()
        raise
# 
# age in years
#   2008: topcause
#   2003: topcause
#   2013: topcause
#
#


def pullCauseByAge():
    conn = sqlite3.connect(MORTALITYDB)
    cur = conn.cursor()


    try: 
        cur.execute("""SELECT Age_Key, 
                            Age_Value, 
                            year, 
                            Cause_Recode_39, 
                            MAX(DeathCount) 
                       FROM (
                            SELECT Age_Key, 
                                Age_Value, 
                                year, 
                                Cause_Recode_39, 
                                COUNT(Cause_Recode_39) as DeathCount
                            FROM mortality
                            WHERE Age_Value != '999'
                            GROUP BY Age_Key, 
                                Age_Value, 
                                year, 
                                Cause_Recode_39
                        )
                        GROUP BY Age_Key, 
                            Age_Value, 
                            year""")
        
        
        jsonData = []
        data = []
        
        for (ageKey, ageValue, year, cause, total,) in  cur.fetchall():
            ageinyears = 0
            if ageKey == u'1':
                ageInYears = float(ageValue)
            elif ageKey == u'2':
                ageInYears = float(ageValue)/12
            elif ageKey == u'4':
                ageInYears = float(ageValue)/365.25
            elif ageKey == u'5':
                ageInYears = float(ageValue)/8670
            elif ageKey == u'6':
                ageInYears = float(ageValue)/525600
   
            data.append({"ageInYears": ageInYears,
                "year": year,
                "cause": int(cause),
                "deathCount": int(total)})

        groupedData = group_by(data, "ageInYears")
        for age in groupedData.keys():
            
            ageJson = {"ageInYears": age,
                "2003": "DNE",
                "2008": "DNE",
                "2013": "DNE"}

            for row in groupedData[age]:
                ageJson[row["year"]] = row["cause"]                

            jsonData.append(ageJson)
            print ageJson
        #Create a dictionary of age key, age vaule -> top cause, top value
        # for (ageKey, ageValue, year, cause, total,) in  cur.fetchall():
        #     jsonData.append({"ageKey": ageKey,
        #         "ageValue": ageValue,
        #         "year": year,
        #         "cause": cause,
        #         "deathCount": total})
        return sorted(jsonData, key= lambda ageJson: ageJson["ageInYears"])

    except: 
        print "ERROR!!!"
        conn.close()
        raise


def pullAverageAgeByCause():
    conn = sqlite3.connect(MORTALITYDB)
    cur = conn.cursor()

    avgAgeData = {}
    try:
        cur.execute("""SELECT mortality.Cause_Recode_39, 
                            mortality.year, 
                            mortality.Age_Key, 
                            AVG(mortality.Age_Value), 
                            COUNT(mortality.Age_Value), 
                            groupcounts.grouptotal 
                        FROM mortality 
                        JOIN (SELECT Cause_Recode_39, 
                                year, COUNT(Age_Key)  as grouptotal
                            FROM mortality
                            WHERE Age_Value != '999'
                            GROUP BY year, Cause_Recode_39) groupcounts
                        ON mortality.Cause_Recode_39 = groupcounts.Cause_Recode_39 and
                            mortality.year = groupcounts.year
                        WHERE mortality.Age_Value != '999' 
                        GROUP BY mortality.Cause_Recode_39, 
                            mortality.year, 
                            mortality.Age_Key """)

        data = [{"cause": int(cause),
            "year": int(year),
            "ageKey": ageKey,
            "avgAge": avgAge,
            "deathCount": deathCount,
            "groupDeathCount": groupDeathCount} for (cause, year, ageKey, avgAge, deathCount, groupDeathCount) in cur.fetchall()]
    
        groupedData = group_by(data, "cause")
        jsonData = []
        for cause in groupedData.keys():
            causeJson = {"cause": cause}
            for row in groupedData[cause]:
                ageinyears = 0
                if row["ageKey"] == u'1':
                    ageInYears = row["avgAge"]
                elif row["ageKey"] == u'2':
                    ageInYears = row["avgAge"]/12
                elif row["ageKey"] == u'4':
                    ageInYears = row["avgAge"]/365.25
                elif row["ageKey"] == u'5':
                    ageInYears = row["avgAge"]/8670
                elif row["ageKey"] == u'6':
                    ageInYears = row["avgAge"]/525600

                if row["year"] in causeJson:
                    causeJson[row["year"]] += (row["deathCount"]/float(row["groupDeathCount"]))*ageInYears
                else:
                    causeJson[row["year"]] = (row["deathCount"]/float(row["groupDeathCount"]))*ageInYears
            jsonData.append(causeJson)
        return sorted(jsonData, key = lambda causeJson: causeJson["cause"])
            
    except:
        print "ERROR!!!"
        conn.close()
        raise

@get("/text")
def ageData ():
    print list(request.query)
    print ("Getting age data")
    topCause = pullCauseByAge()
    avgAge = pullAverageAgeByCause()
    return {"TopCauseByAge": topCause,
        "AverageAgeForCause": avgAge}

# URI for getting data
# pass a gender argument as:
#    data?gender=M  
#    data?gender=F
#    data?gender=
#
# Return the result in JSON format


# URI for getting data for visualization
@get("/data")
def vizData ():
    return {"vizdata": pullVizData()} #make code happy with formatting
    
# URI for getting a static file from the
# server
# For instance, mortality-demo.html

@get('/<name>')
def static (name="index.html"):
    return static_file(name, root='.')


# main entry point
# run the server on the given port

def main (p):
    run(host='0.0.0.0', port=p)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(int(sys.argv[1]))
    else:
        print "Usage: server <port>"
