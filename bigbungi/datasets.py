"""Original, deterministic synthetic data; no copied examination datasets."""
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.model_selection import train_test_split

VERSION = "2026.2"


def generate(root: Path) -> dict:
    rng = np.random.default_rng(41027)
    root.mkdir(parents=True, exist_ok=True)
    datasets: dict[str, dict[str, pd.DataFrame]] = {}
    private = {}

    def add(pid, **frames):
        datasets[pid] = frames

    n = 360
    add("t1-01", customers=pd.DataFrame({"id": range(1, n + 1), "age": rng.integers(20, 90, n), "score": rng.lognormal(3.8, .6, n).round(3), "region": rng.choice(["서울", "부산", "대전", "광주"], n)}))
    n = 480
    income = rng.normal(5200, 1350, n).round(2)
    income[rng.choice(n, 43, replace=False)] = np.nan
    add("t1-02", members=pd.DataFrame({"member_id": range(1, n+1), "age": rng.integers(20, 75, n), "income": income, "spending": rng.integers(100, 2000, n)}))
    n = 620
    amounts = rng.lognormal(4.5, .6, n).round(2)
    amounts[rng.choice(n, 14, replace=False)] *= 6
    add("t1-03", deliveries=pd.DataFrame({"order_id": range(1,n+1), "region": rng.choice(["서울", "경기", "부산"],n), "delivery_minutes": amounts, "distance_km": rng.uniform(1, 30, n).round(2)}))
    n = 1200
    cancelled = rng.random(n) < .19
    add("t1-04", transactions=pd.DataFrame({"transaction_code": [f"{'C' if c else 'T'}{i:05d}" for i,c in enumerate(cancelled,1)], "customer_id": rng.integers(1001,1081,n), "product_code": rng.choice(["P01","P02","P03","P04","P05"],n), "amount": rng.integers(10,150,n)*1000}))
    n = 900
    add("t1-05", visits=pd.DataFrame({"visit_id": range(1,n+1), "visited_at": pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 365*24, n), unit="h"), "channel": rng.choice(["검색","광고","직접"],n), "purchase_amount": rng.choice([0,15000,28000,45000,72000],n)}))
    n = 560
    customers = pd.DataFrame({"customer_id": range(1,181), "grade": rng.choice(["일반","우수","VIP"],180), "region": rng.choice(["서울","경기","부산"],180)})
    orders = pd.DataFrame({"order_id": range(1,n+1), "customer_id": rng.integers(1,181,n), "amount": rng.integers(10,100,n)*1000, "status": rng.choice(["완료","취소"],n,p=[.84,.16])})
    add("t1-06", customers=customers, orders=orders)
    n = 420
    add("t1-07", sensors=pd.DataFrame({"sensor_id":range(1,n+1), "temperature":rng.normal(24,4,n).round(4), "humidity":rng.uniform(20,90,n).round(4), "energy":rng.lognormal(4.2,.3,n).round(4)}))
    n = 760
    sales = rng.integers(10,600,n)*100
    quantity = rng.integers(1,8,n)
    add("t1-08", sales=pd.DataFrame({"record_id":range(1,n+1), "store":rng.choice(["강남","잠실","홍대","종로","판교","서면"],n), "category":rng.choice(["식품","생활","가전"],n), "sales":sales, "quantity":quantity}))
    n = 360
    f = rng.normal(55,12,n).round(4)
    f[rng.choice(n, 9, replace=False)] += 80
    add("t1-09", measurements=pd.DataFrame({"id":range(1,n+1), "value":f, "batch":rng.choice(["A","B","C"],n)}))
    dates = pd.date_range("2020-01-01", "2025-12-01",freq="MS")
    rows = [(d.year,d.month,r,c,round(1400*(1.09**(d.year-2020))*rng.uniform(.75,1.35),3)) for d in dates for r in ["한국","일본","독일","미국"] for c in ["제조","운송"]]
    add("t1-10", emissions=pd.DataFrame(rows,columns=["year","month","country","sector","emission"]))

    # Prediction tasks: labels use nonlinear signal plus irreducible noise.
    n = 2200
    age=rng.integers(20,75,n); tenure=rng.integers(1,73,n)
    contract=rng.choice(["monthly","annual","two_year"],n,p=[.5,.3,.2])
    charge=rng.uniform(25,135,n); support=rng.poisson(1.4,n)
    usage=np.clip(rng.normal(60,20,n),3,140)
    logits=-1.5 + 1.5*(contract=="monthly") - .018*tenure + .022*(charge-70) + .43*support - .016*(usage-60) + .4*(age>60)
    target=rng.binomial(1,expit(logits))
    frame=pd.DataFrame({"id":range(10001,10001+n),"age":age,"tenure_months":tenure,"monthly_charge":charge.round(2),"contract":contract,"support_calls":support,"usage_gb":usage.round(2)})
    for col in ["age","usage_gb"]: frame.loc[rng.choice(n,70,False),col]=np.nan
    split_prediction("t2-01",frame,target,"churn",datasets,private)

    n=2400
    area=rng.uniform(25,180,n); rooms=rng.integers(1,6,n); age=rng.integers(0,35,n)
    station=rng.uniform(.05,4,n); district=rng.choice(["central","north","south","west"],n)
    premium=np.select([district=="central",district=="south",district=="north"],[1400,650,150],default=0)
    rent=600+area*22+rooms*80-age*13-station*130+premium+250*np.sin(area/35)+rng.normal(0,200,n)
    frame=pd.DataFrame({"id":range(20001,20001+n),"area_m2":area.round(2),"rooms":rooms,"building_age":age,"station_km":station.round(3),"district":district,"floor":rng.integers(1,26,n)})
    for col in ["area_m2","station_km"]: frame.loc[rng.choice(n,50,False),col]=np.nan
    split_prediction("t2-02",frame,np.round(np.maximum(rent,300),2),"monthly_rent",datasets,private)

    n=2200
    play=rng.gamma(4,4,n); wins=rng.uniform(.1,.95,n); quests=rng.poisson(15,n); spending=rng.gamma(2,20,n)
    device=rng.choice(["pc","mobile","console"],n)
    latent=.06*play+3.0*wins+.065*quests+.004*spending+.45*(device=="pc")+rng.normal(0,.37,n)
    target=np.digitize(latent,[3.35,4.45])
    frame=pd.DataFrame({"id":range(30001,30001+n),"weekly_hours":play.round(2),"win_rate":wins.round(3),"quests_completed":quests,"spend_usd":spending.round(2),"device":device,"days_active":rng.integers(3,1000,n)})
    frame.loc[rng.choice(n,80,False),"weekly_hours"]=np.nan
    split_prediction("t2-03",frame,target,"level",datasets,private)

    n=180
    group=rng.choice(["A","B","C"],n)
    before=rng.normal(145,12,n)
    improvement=np.select([group=="A",group=="B"],[3.5,6.5],default=8.2)+rng.normal(0,7,n)
    add("t3-01", treatment=pd.DataFrame({"patient_id":range(1,n+1),"group":group,"before":before.round(3),"after":(before-improvement).round(3)}))
    n=320
    spend=rng.uniform(10,100,n); visits=spend*4+rng.normal(200,70,n); time=rng.normal(300,45,n); clicks=visits*.12+rng.normal(0,8,n)
    revenue=1000+spend*32+visits*2.8+time*.9+clicks*4+rng.normal(0,180,n)
    add("t3-02", promotion=pd.DataFrame({"ad_spend":spend.round(3),"visits":visits.round(3),"page_time":time.round(3),"clicks":clicks.round(3),"sales":revenue.round(3)}))
    n=650
    age=rng.integers(22,75,n); history=rng.choice(["No","Pre","Yes"],n,p=[.45,.3,.25]); glucose=rng.integers(75,190,n)
    risk=expit(-3.4+.043*age+.65*(history=="Pre")+1.3*(history=="Yes"))
    outcome=rng.binomial(1,risk)
    add("t3-03", screening=pd.DataFrame({"id":range(1,n+1),"age":age,"history":history,"glucose":glucose,"outcome":outcome}))

    from .extra_datasets import generate_additional
    generate_additional(datasets, private, split_prediction)

    for pid,frames in datasets.items():
        directory=root/pid; directory.mkdir(exist_ok=True)
        for name,df in frames.items():
            df.to_csv(directory/f"{name}.csv",index=False,float_format="%.6f")
    (root/"private.json").write_text(json.dumps({"version":VERSION,"targets":private},ensure_ascii=False),encoding="utf-8")
    return private


def split_prediction(pid,frame,target,target_name,datasets,private,*,classification=None):
    if classification is None: classification = pid != "t2-02"
    stratify=target if classification else None
    train_idx,test_idx=train_test_split(np.arange(len(frame)),test_size=.25,random_state=42,stratify=stratify)
    train=frame.iloc[train_idx].copy(); train[target_name]=np.asarray(target)[train_idx]
    test=frame.iloc[test_idx].copy()
    datasets[pid]={"train":train,"test":test}
    private[pid]={"ids":test["id"].astype(int).tolist(),"y":np.asarray(target)[test_idx].tolist()}


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,default=Path(".runtime/datasets")); args=parser.parse_args()
    generate(args.output)
    print(f"Generated 50 deterministic datasets in {args.output}")
