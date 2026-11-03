"""Build static content and evaluate trusted reference answers against saved CSVs."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

import pandas as pd

from .content import PROBLEMS
from .datasets import generate, VERSION

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/".runtime"/"datasets"
PUBLIC=ROOT/"web"/"public"/"content"


def reference_result(problem, directory):
    with tempfile.TemporaryDirectory(prefix="bigbungi-solution-") as tmp:
        work=Path(tmp)
        shutil.copytree(directory,work/"data")
        result=work/"answer.json"
        script=problem["solution"]+'\nimport json\nfrom pathlib import Path\nPath("answer.json").write_text(json.dumps(answers), encoding="utf-8")\n'
        env={**os.environ,"OPENBLAS_NUM_THREADS":"1","OMP_NUM_THREADS":"1","MPLBACKEND":"Agg"}
        proc=subprocess.run([sys.executable,"-c",script],cwd=work,capture_output=True,text=True,timeout=30,env=env)
        if proc.returncode: raise RuntimeError(f"Reference failed: {problem['id']}\n{proc.stderr}")
        return json.loads(result.read_text())


def prepare(force=False):
    sources=["content.py","datasets.py","extra_content.py","extra_datasets.py"]
    fingerprint=hashlib.sha256(b"".join((ROOT/"bigbungi"/name).read_bytes() for name in sources)).hexdigest()
    marker=PUBLIC/"build.json"
    if not force and marker.exists() and json.loads(marker.read_text()).get("fingerprint")==fingerprint:
        print(f"Static content is current ({len(PROBLEMS)} exercises).")
        return
    targets=generate(DATA)
    PUBLIC.mkdir(parents=True,exist_ok=True)
    (PUBLIC/"problems").mkdir(exist_ok=True)
    (PUBLIC/"solutions").mkdir(exist_ok=True)
    grading={}
    catalog=[]
    for p in PROBLEMS:
        pid=p["id"]
        public={k:v for k,v in p.items() if k not in ["solution","explanation"]}
        for spec in public["files"]:
            df=pd.read_csv(DATA/pid/spec["name"])
            spec["rows"]=len(df)
            spec["missing"]=int(df.isna().sum().sum())
            spec["preview"]=json.loads(df.head(8).to_json(orient="records",force_ascii=False))
        (PUBLIC/"problems"/f"{pid}.json").write_text(json.dumps(public,ensure_ascii=False),encoding="utf-8")
        (PUBLIC/"solutions"/f"{pid}.json").write_text(json.dumps({"code":p["solution"],"explanation":p["explanation"]},ensure_ascii=False),encoding="utf-8")
        if p["type"]==2:
            grading[pid]={"type":2,**p["submission"],**targets[pid]}
        else:
            grading[pid]={"type":p["type"],"expected":reference_result(p,DATA/pid),"fields":p["fields"]}
        catalog.append({k:public[k] for k in ["id","type","number","title","difficulty","minutes","tags","points"]})
        dest=PUBLIC/"data"/pid
        dest.mkdir(parents=True,exist_ok=True)
        for f in p["files"]: shutil.copyfile(DATA/pid/f["name"],dest/f["name"])
    (PUBLIC/"catalog.json").write_text(json.dumps(catalog,ensure_ascii=False),encoding="utf-8")
    (PUBLIC/"grading.json").write_text(json.dumps(grading,ensure_ascii=False),encoding="utf-8")
    marker.write_text(json.dumps({"version":VERSION,"fingerprint":fingerprint,"problems":len(catalog)}))
    print(f"Built {len(catalog)} exercises, CSVs, solutions and grading keys in {PUBLIC}")


if __name__=="__main__":
    prepare("--force" in sys.argv)
