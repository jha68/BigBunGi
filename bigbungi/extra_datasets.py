"""Additional original datasets. Independent seeds preserve the original exercises."""
import numpy as np
import pandas as pd
from scipy.special import expit


def generate_additional(datasets, private, split_prediction):
    def rng_for(pid):
        return np.random.default_rng(73000 + int(pid[1]) * 100 + int(pid[-2:]))

    def add(pid, **frames):
        datasets[pid] = frames

    r = rng_for("t1-11"); n = 520
    frame = pd.DataFrame({"record_id": np.arange(1,n+1), "user_id": r.integers(1,181,n),
        "updated_at": pd.Timestamp("2025-01-01") + pd.to_timedelta(r.integers(0,8500,n),unit="h"),
        "status": r.choice(["active","inactive"],n,p=[.78,.22]), "minutes": r.gamma(4,12,n).round(2)})
    frame.loc[:1,"user_id"] = 1; frame.loc[:1,"updated_at"] = pd.Timestamp("2025-12-31")
    add("t1-11", sessions=frame)
    r = rng_for("t1-12"); n = 420
    dept = r.choice(["영업","개발","지원","기획"],n)
    bonus = r.normal(200 + (dept=="영업")*60,40,n).round(2)
    bonus[r.choice(n,55,False)] = np.nan
    add("t1-12", employees=pd.DataFrame({"id":range(1,n+1),"department":dept,"bonus":bonus,"rating":r.uniform(1,5,n).round(2)}))
    r = rng_for("t1-13"); n = 450
    frame = pd.DataFrame({"id":range(1,n+1),**{f"k{i}":r.normal(50+i*5,8,n).round(3) for i in range(1,6)}})
    for col,count in zip(["k1","k2","k3","k4"],[10,20,95,150]): frame.loc[r.choice(n,count,False),col] = np.nan
    add("t1-13", quality=frame)
    r = rng_for("t1-14"); n = 560
    values = r.lognormal(3.3,.6,n).round(3); values[r.choice(n,14,False)] = np.nan
    add("t1-14", readings=pd.DataFrame({"id":range(1,n+1),"value":values}))
    r = rng_for("t1-15"); n = 600
    add("t1-15", payments=pd.DataFrame({"id":range(1,n+1),"amount":[f"{v:,}원" for v in r.integers(10,300,n)*100],
        "discount":r.choice(["0%","5%","10%","15%","20%"],n),"channel":r.choice(["온라인","매장"],n),"status":r.choice(["결제","취소"],n,p=[.83,.17])}))
    r = rng_for("t1-16"); n = 500
    sent = pd.Timestamp("2025-03-01") + pd.to_timedelta(r.integers(0,90*24,n),unit="h")
    add("t1-16", parcels=pd.DataFrame({"id":range(1,n+1),"shipped_at":sent,"arrived_at":sent+pd.to_timedelta(r.integers(12,101,n),unit="h")}))
    r = rng_for("t1-17"); dates = pd.date_range("2024-01-01","2025-06-30"); n = len(dates)
    add("t1-17", retail=pd.DataFrame({"date":dates,"revenue":(r.gamma(5,6000,n)*(1+dates.month.to_numpy()/20)).round(2)}))
    r = rng_for("t1-18"); n = 720
    add("t1-18", rankings=pd.DataFrame({"id":range(1,n+1),"region":r.choice(["서울","경기","부산","대전","광주"],n),"score":r.integers(40,101,n)}))
    r = rng_for("t1-19"); n = 800
    add("t1-19", channels=pd.DataFrame({"id":range(1,n+1),"store_id":r.integers(1,9,n),"channel":r.choice(["온라인","오프라인"],n),"sales":r.integers(10,800,n)*100}))
    r = rng_for("t1-20"); n = 800
    add("t1-20", suppliers=pd.DataFrame({"supplier_id":range(1,181),"grade":r.choice(["A","B","C"],180)}),
        purchases=pd.DataFrame({"purchase_id":range(1,n+1),"supplier_id":r.integers(1,196,n),"cost":r.integers(20,400,n)*1000,"status":r.choice(["입고","대기"],n,p=[.8,.2])}))
    r = rng_for("t1-21"); n = 480
    price = r.uniform(1000,15000,n).round(2); price[r.choice(n,12,False)] = np.nan
    add("t1-21", inventory=pd.DataFrame({"id":range(1,n+1),"unit_price":price,"quantity":r.integers(0,21,n)}))
    r = rng_for("t1-22"); n = 900
    add("t1-22", orders=pd.DataFrame({"id":range(1,n+1),"customer_id":r.integers(1,331,n),"status":r.choice(["완료","취소"],n,p=[.78,.22]),"amount":r.integers(10,500,n)*100}))
    r = rng_for("t1-23"); n = 640
    channel = r.choice(["전화","채팅","이메일"],n)
    add("t1-23", claims=pd.DataFrame({"id":range(1,n+1),"channel":channel,"refunded":r.binomial(1,np.select([channel=="전화",channel=="채팅"],[.3,.45],default=.2))}))
    r = rng_for("t1-24"); n = 500
    a = r.normal(50,10,n); b = -a*.7+r.normal(55,9,n); c = r.normal(30,6,n)
    frame = pd.DataFrame({"id":range(1,n+1),"chem_a":a,"chem_b":b,"chem_c":c,"chem_d":r.normal(70,10,n),"yield_score":.5*a-1.2*b+.05*c+r.normal(0,8,n)}).round(4)
    for col in ["chem_a","chem_b","chem_c","chem_d","yield_score"]: frame.loc[r.choice(n,9,False),col] = np.nan
    add("t1-24", laboratory=frame)
    r = rng_for("t1-25"); n = 600
    age = r.integers(18,81,n); age[:5] = [18,30,45,60,80]
    add("t1-25", health=pd.DataFrame({"id":range(1,n+1),"age":age,"glucose":(80+.6*age+r.normal(0,12,n)).round(2)}))
    r = rng_for("t1-26"); rows=[]
    for shop in range(1,101):
        base = r.uniform(30000,150000); growth = r.uniform(.85,1.4)
        for year in [2024,2025]:
            for product in ["A","B","C"]: rows.append((shop,year,product,round(base*(growth if year==2025 else 1)*r.uniform(.8,1.2),2)))
    add("t1-26", annual_sales=pd.DataFrame(rows,columns=["store_id","year","product","sales"]))
    r = rng_for("t1-27"); n = 520
    domains = r.choice(["corp.co.kr","mail.com","study.net"],180)
    addresses = [f"user{i+1:03d}@{domain}" for i,domain in enumerate(domains)]
    email = [addresses[int(i)] for i in r.integers(0,180,n)]
    email = [(" "+e.upper()+" ") if i%3==0 else e for i,e in enumerate(email)]
    for i in range(0,n,57): email[i] = "invalid-address"
    add("t1-27", accounts=pd.DataFrame({"record_id":range(1,n+1),"email":email,"login_count":r.integers(1,200,n)}))
    r = rng_for("t1-28"); n = 365
    add("t1-28", energy=pd.DataFrame({"date":pd.date_range("2025-01-01",periods=n),"consumption":(120+20*np.sin(np.arange(n)/25)+r.normal(0,10,n)).round(3)}))
    r = rng_for("t1-29"); n = 600
    add("t1-29", shipments=pd.DataFrame({"order_id":range(1,n+1),"customer_id":r.integers(1,51,n),"ordered_at":pd.Timestamp("2025-01-01")+pd.to_timedelta(r.integers(0,200*24,n),unit="h"),"quantity":r.integers(1,21,n)}))
    r = rng_for("t1-30"); n = 500
    frame = pd.DataFrame({"id":range(1,n+1),"amount_a":r.lognormal(4,1.15,n),"amount_b":r.gamma(6,8,n),"amount_c":r.uniform(10,90,n)}).round(4)
    for col in ["amount_a","amount_b","amount_c"]: frame.loc[r.choice(n,10,False),col] = np.nan
    add("t1-30", amounts=frame)

    def prediction(pid, frame, target, target_name, classification=True, novel=None):
        r = rng_for(pid)
        for col in frame.select_dtypes(include="number").columns:
            if col != "id": frame.loc[r.choice(len(frame),int(len(frame)*.025),False),col] = np.nan
        for col in frame.select_dtypes(exclude="number").columns:
            frame.loc[r.choice(len(frame),int(len(frame)*.015),False),col] = np.nan
        split_prediction(pid,frame,target,target_name,datasets,private,classification=classification)
        if novel:
            column,value = novel
            test = datasets[pid]["test"]
            test.loc[test.index[:3],column] = value

    r = rng_for("t2-04"); n = 2200
    age=r.integers(20,85,n); stay=r.integers(1,22,n); prior=r.poisson(1,n); chronic=r.integers(0,5,n)
    discharge=r.choice(["home","clinic","facility"],n); follow=r.binomial(1,.65,n)
    y=r.binomial(1,expit(-4+.035*(age-45)+.11*stay+.9*prior+.75*chronic-.9*follow+.6*(discharge=="facility")))
    frame=pd.DataFrame({"id":range(40001,40001+n),"age":age,"stay_days":stay,"prior_admissions":prior,"chronic_count":chronic,"discharge":discharge,"followup":follow})
    prediction("t2-04",frame,y,"readmitted",novel=("discharge","other"))
    r = rng_for("t2-05"); n = 2400
    age=r.integers(0,16,n); mileage=r.uniform(1000,180000,n); engine=r.choice([1000,1600,2000,2500,3000],n); brand=r.choice(["A","B","C","D"],n); fuel=r.choice(["gas","diesel","hybrid"],n); accident=r.poisson(.4,n)
    price=np.maximum(150,1200+engine*.6-age*95-mileage*.004+900*(brand=="A")+450*(brand=="B")+350*(fuel=="hybrid")-180*accident+r.normal(0,130,n))
    frame=pd.DataFrame({"id":range(50001,50001+n),"vehicle_age":age,"mileage_km":mileage.round(1),"engine_cc":engine,"brand":brand,"fuel":fuel,"accidents":accident})
    prediction("t2-05",frame,price.round(2),"resale_price",classification=False)
    r = rng_for("t2-06"); n = 2200
    alcohol=r.uniform(8,15,n); acidity=r.uniform(2.8,4,n); sugar=r.gamma(2,2,n); sulphates=r.uniform(.3,1.2,n); grape=r.choice(["red","white","rose"],n)
    latent=.65*(alcohol-11)-1.4*(acidity-3.3)+1.1*(sulphates-.6)-.08*sugar+.3*(grape=="red")+r.normal(0,.28,n)
    y=np.digitize(latent,[-.45,.9])
    frame=pd.DataFrame({"id":range(60001,60001+n),"alcohol":alcohol.round(3),"acidity":acidity.round(3),"residual_sugar":sugar.round(3),"sulphates":sulphates.round(3),"grape":grape,"region":r.choice(["north","south","west"],n)})
    prediction("t2-06",frame,y,"quality_class")
    r = rng_for("t2-07"); n = 2400
    spend=r.gamma(3,80,n); recency=r.integers(1,181,n); visits=r.poisson(5,n); discount=r.choice([0,5,10,20,30],n); channel=r.choice(["email","sms","app"],n)
    y=r.binomial(1,expit(-2+.004*(spend-200)-.018*(recency-60)+.3*(visits-4)+.08*discount+.8*(channel=="app")))
    frame=pd.DataFrame({"id":range(70001,70001+n),"previous_spend":spend.round(2),"days_since_purchase":recency,"visits":visits,"discount_pct":discount,"channel":channel,"device":r.choice(["pc","mobile"],n)})
    prediction("t2-07",frame,y,"responded")
    r = rng_for("t2-08"); n = 2200
    distance=r.uniform(.5,25,n); traffic=r.uniform(0,1,n); weight=r.gamma(2,1.2,n); rain=r.binomial(1,.25,n); zone=r.choice(["central","east","west"],n); hour=r.integers(8,23,n)
    duration=12+distance*2.8+traffic*18+np.sqrt(weight)*2+rain*6+5*(zone=="central")+4*((hour>=17)&(hour<=20))+r.normal(0,2.8,n)
    frame=pd.DataFrame({"id":range(80001,80001+n),"distance_km":distance.round(3),"traffic_index":traffic.round(3),"weight_kg":weight.round(3),"rain":rain,"zone":zone,"hour":hour})
    prediction("t2-08",frame,duration.round(3),"duration_minutes",classification=False)
    r = rng_for("t2-09"); n = 2400
    temperature=r.normal(65,12,n); vibration=r.gamma(2,1,n); hours=r.uniform(100,12000,n); maintenance=r.integers(1,181,n); machine=r.choice(["A","B","C"],n)
    y=r.binomial(1,expit(-3+.07*(temperature-60)+1.0*(vibration-1.5)+.00014*hours+.014*(maintenance-60)+.8*(machine=="C")))
    frame=pd.DataFrame({"id":range(90001,90001+n),"temperature":temperature.round(3),"vibration":vibration.round(3),"operating_hours":hours.round(2),"days_since_service":maintenance,"machine_type":machine,"site":r.choice(["east","west","south"],n)})
    prediction("t2-09",frame,y,"failed")
    r = rng_for("t2-10"); n = 2400
    debt=r.uniform(.05,.85,n); delinquency=r.poisson(.6,n); score=r.integers(450,901,n); years=r.integers(0,31,n); income=r.lognormal(8.6,.5,n); residence=r.choice(["own","rent","family"],n)
    latent=3.5*debt+.65*delinquency-.007*(score-650)-.025*years-.00004*(income-5000)+.25*(residence=="rent")+r.normal(0,.28,n)
    y=np.digitize(latent,[1.0,2.5])
    frame=pd.DataFrame({"id":range(100001,100001+n),"debt_ratio":debt.round(4),"delinquencies":delinquency,"credit_score":score,"employment_years":years,"income":income.round(2),"residence":residence})
    prediction("t2-10",frame,y,"risk_class")

    r = rng_for("t3-04"); group=np.array(["A"]*120+["B"]*140); n=len(group)
    score=np.r_[r.normal(68,7,120),r.normal(72,14,140)].round(3);score[r.choice(n,10,False)]=np.nan
    add("t3-04", results=pd.DataFrame({"id":range(1,n+1),"group":group,"score":score}))
    r = rng_for("t3-05"); n=600
    add("t3-05", acquisition=pd.DataFrame({"id":range(1,n+1),"channel":r.choice(["검색","광고","직접","추천"],n,p=[.36,.33,.22,.09])}))
    r = rng_for("t3-06"); n=240
    hours=r.uniform(5,65,n)
    add("t3-06", training=pd.DataFrame({"id":range(1,n+1),"hours":hours.round(3),"tenure":r.integers(1,20,n),"score":(35+.7*hours+r.normal(0,7,n)).round(3)}))
    r = rng_for("t3-07"); n=650
    age=r.integers(22,76,n); exercise=r.integers(0,8,n); smoker=r.choice(["No","Yes"],n,p=[.65,.35])
    y=r.binomial(1,expit(-2.2+.035*age-.3*exercise+.9*(smoker=="Yes")))
    add("t3-07", lifestyle=pd.DataFrame({"id":range(1,n+1),"age":age,"exercise":exercise,"smoker":smoker,"sugar":r.uniform(70,170,n).round(2),"outcome":y}))
    r = rng_for("t3-08"); n=800
    group=np.array(["A"]*400+["B"]*400)
    add("t3-08", experiment=pd.DataFrame({"id":range(1,n+1),"group":group,"converted":r.binomial(1,np.where(group=="A",.24,.30))}))
    r = rng_for("t3-09"); n=280
    hours=r.uniform(.5,30,n); score=(35+15*np.log1p(hours)+r.normal(0,5,n)).round(3)
    frame=pd.DataFrame({"id":range(1,n+1),"study_hours":hours.round(3),"score":score})
    for col in ["study_hours","score"]:frame.loc[r.choice(n,7,False),col]=np.nan
    add("t3-09", study=frame)
    r = rng_for("t3-10"); n=300
    area=r.uniform(40,250,n); staff=np.maximum(1,np.rint(area/20+r.normal(0,2,n))); ads=r.uniform(10,100,n)
    add("t3-10", stores=pd.DataFrame({"id":range(1,n+1),"area":area.round(3),"staff":staff.astype(int),"ad_spend":ads.round(3),"sales":(500+9*area+50*staff+1.1*ads+r.normal(0,180,n)).round(3)}))
