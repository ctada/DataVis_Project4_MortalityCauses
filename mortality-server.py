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

def pullData (gender):
    # ignore age & gender for now
    conn = sqlite3.connect(MORTALITYDB)
    cur = conn.cursor()

    try: 
        if gender:
            cur.execute("""SELECT year, Cause_Recode_39, SUM(1) as total 
                           FROM mortality
                           WHERE sex = '%s'
                           GROUP BY year, Cause_Recode_39""" % (gender))
        else:
            cur.execute("""SELECT year, Cause_Recode_39, SUM(1) as total 
                           FROM mortality
                           GROUP BY year, Cause_Recode_39""")
        data = [{"year":int(year),
                 "cause":int(cause),
                 "total":total} for (year, cause, total,) in  cur.fetchall()]
        grouped_data = group_by(data,"cause")
        for cause in grouped_data:
            grouped_data[cause]= group_by(grouped_data[cause],"year")
        conn.close()
        return grouped_data

    except: 
        print "ERROR!!!"
        conn.close()
        raise

def pullCauseByAge():
    conn = sqlite3.connect(MORTALITYDB)
    cur = conn.cursor()


    try: 
        cur.execute("""SELECT Age_Key, Age_Value, year, Cause_Recode_39, COUNT(Cause_Recode_39) 
                       FROM mortality
                       WHERE Age_Value != '999'
                       GROUP BY Age_Key, Age_Value, year, Cause_Recode_39""")
        
        data = {}
        #Create a dictionary of age key, age vaule -> top cause, top value
        for (ageKey, ageValue, year, cause, total,) in  cur.fetchall():
            if (ageKey in data):
                if ageValue in data[ageKey]:
                    if year in data[ageKey][ageValue]:
                        if (int(total) > data[ageKey][ageValue][year]["total"]):
                            data[ageKey][ageValue][year]["total"] = int(total)
                            data[ageKey][ageValue][year]["cause"] = int(cause)
                    else:
                        data[ageKey][ageValue][year] = {}
                        data[ageKey][ageValue][year]["total"] = int(total)
                        data[ageKey][ageValue][year]["cause"] = int(cause)
                else:
                    data[ageKey][ageValue] = {}
                    data[ageKey][ageValue][year] = {}
                    data[ageKey][ageValue][year]["total"] = int(total)
                    data[ageKey][ageValue][year]["cause"] = int(cause)
            else:
                data[ageKey] = {}
                data[ageKey][ageValue] = {}
                data[ageKey][ageValue][year] = {}
                data[ageKey][ageValue][year]["total"] = int(total)
                data[ageKey][ageValue][year]["cause"] = int(cause)

        jsonData = []
        for ageKey in data.keys():
            for ageValue in data[ageKey].keys():
                for year in data[ageKey][ageValue].keys():
                    jsonData.append({
                        "ageKey": ageKey,
                        "ageValue": ageValue,
                        "year": year,
                        "total": data[ageKey][ageValue][year]["total"],
                        "cause": data[ageKey][ageValue][year]["total"]
                        })

        return jsonData


    except: 
        print "ERROR!!!"
        conn.close()
        raise

def pullAgeData():
    conn = sqlite3.connect(MORTALITYDB)
    cur = conn.cursor()

    avgAgeData = {}
    try:
        cur.execute("""SELECT year, Cause_Recode_39, Age_Key, AVG(Age_Value), COUNT(Age_Value) 
                        FROM mortality
                        WHERE Age_Value != '999'
                        GROUP BY year, Cause_Recode_39, Age_Key""")
        data = [{"year":int(year),
                 "cause":int(cause),
                 "ageKey":ageKey,
                 "avgAge":avgAge,
                 "numResp": numResp} for (year, cause, ageKey, avgAge, numResp) in  cur.fetchall()]
        grouped_data = group_by(data,"cause")
        for cause in grouped_data:
            grouped_data[cause]= group_by(grouped_data[cause],"year")
        for cause in grouped_data:
            for year in grouped_data[cause]:
                totalResp = 0
                for i, row in enumerate(grouped_data[cause][year]):
                    if row["ageKey"] == u'1':
                        grouped_data[cause][year][i]["ageInYears"] = row["avgAge"]
                        totalResp += row["numResp"]
                    elif row["ageKey"] == u'2':
                        grouped_data[cause][year][i]["ageInYears"] = row["avgAge"]/12
                        totalResp += row["numResp"]
                    elif row["ageKey"] == u'4':
                        grouped_data[cause][year][i]["ageInYears"] = row["avgAge"]/365.25
                        totalResp += row["numResp"]
                    elif row["ageKey"] == u'5':
                        grouped_data[cause][year][i]["ageInYears"] = row["avgAge"]/8670
                        totalResp += row["numResp"]
                    elif row["ageKey"] == u'6':
                        grouped_data[cause][year][i]["ageInYears"] = row["avgAge"]/525600
                        totalResp += row["numResp"]
                for i, row in enumerate(grouped_data[cause][year]):
                    if cause in avgAgeData:
                        if year in avgAgeData[cause]:
                            avgAgeData[cause][year] += row["avgAge"] * row["numResp"]/totalResp
                        else: 
                            avgAgeData[cause][year] = row["avgAge"] * row["numResp"]/totalResp
                    else:
                        avgAgeData[cause] = {}
                        avgAgeData[cause][year] = row["avgAge"] * row["numResp"]/totalResp
        return avgAgeData
    except:
        print "ERROR!!!"
        conn.close()
        raise
        
@get("/text")
def ageData ():
    print list(request.query)
    print ("Getting age data")
    pullCauseByAge()
    # return pullAgeData()
# URI for getting data
# pass a gender argument as:
#    data?gender=M  
#    data?gender=F
#    data?gender=
#
# Return the result in JSON format

@get("/data")
def data ():
    print list(request.query)
    gender = request.query.gender

    print "gender =", gender
    return pullData(gender)

    
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
