import json
import hashlib
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, f1_score, mean_squared_error

from bigbungi.content import PROBLEMS
from bigbungi.prepare import DATA, PUBLIC, reference_result, prepare
from bigbungi.datasets import generate


def original_problem_hash(problem):
    """Exclude only metadata which prepare() adds to the in-memory file specs."""
    p = json.loads(json.dumps(problem))
    for file in p['files']:
        for key in ('rows', 'missing', 'preview'):
            file.pop(key, None)
    return hashlib.sha256(json.dumps(p, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class ContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        prepare()
        cls.keys=json.loads((PUBLIC/"grading.json").read_text())

    def test_requested_curriculum_and_contracts(self):
        self.assertEqual([sum(p['type']==t for p in PROBLEMS) for t in [1,2,3]],[30,10,10])
        self.assertEqual({p['id'] for p in PROBLEMS}, {f"t{kind}-{number:02d}" for kind,count in [(1,30),(2,10),(3,10)] for number in range(1,count+1)})
        for p in PROBLEMS:
            with self.subTest(problem=p['id']):
                public=json.loads((PUBLIC/'problems'/f"{p['id']}.json").read_text())
                self.assertNotIn('solution',public)
                self.assertNotIn('expected',public)
                self.assertTrue(p['steps'])
                for f in p['files']:
                    df=pd.read_csv(DATA/p['id']/f['name'])
                    self.assertGreater(len(df),100)
                    self.assertEqual(list(df.columns),[c['name'] for c in f['columns']])

    def test_previously_solved_questions_are_preserved(self):
        snapshot = json.loads((Path(__file__).parent / 'preserved_questions.json').read_text())
        for p in PROBLEMS:
            if p['id'] not in snapshot:
                continue
            with self.subTest(problem=p['id']):
                saved = snapshot[p['id']]
                self.assertEqual(original_problem_hash(p), saved['problem_sha256'])
                self.assertEqual(self.keys[p['id']], saved['grading'])
                for filename, digest in saved['csv_sha256'].items():
                    for directory in (DATA, PUBLIC / 'data'):
                        self.assertEqual(hashlib.sha256((directory / p['id'] / filename).read_bytes()).hexdigest(), digest)

    def test_revised_answer_contracts_and_prediction_requirements(self):
        for p in PROBLEMS:
            with self.subTest(problem=p['id']):
                if p['type'] == 1 and p['number'] >= 9:
                    self.assertEqual(len(p['fields']), 1)
                elif p['type'] == 3:
                    self.assertEqual(len(p['steps']), 3)
                    self.assertEqual(len(p['fields']), 3)
                elif p['type'] == 2:
                    text = '\n'.join(p['steps'])
                    self.assertIn(p['submission']['target'], text)
                    self.assertIn(p['submission']['prediction'], text)
                    self.assertIn(p['submission']['metric'].upper(), text)
                    self.assertIn('submission.csv', text)
                    self.assertNotIn('predict_proba', text)
                    self.assertNotIn('fit', text)
                    self.assertNotIn('Pipeline', text)

    def test_numeric_references_against_actual_csvs(self):
        for p in PROBLEMS:
            if p['type']==2: continue
            with self.subTest(problem=p['id']):
                computed=reference_result(p,DATA/p['id'])
                self.assertEqual(set(computed),{f['key'] for f in p['fields']})
                for value in computed.values(): self.assertTrue(math.isfinite(value))
                self.assertEqual(computed,self.keys[p['id']]['expected'])

    def test_prediction_references_meet_learning_thresholds(self):
        for p in PROBLEMS:
            if p['type']!=2:continue
            with self.subTest(problem=p['id']),tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp);shutil.copytree(DATA/p['id'],directory/'data')
                result=subprocess.run([sys.executable,'-c',p['solution']],cwd=directory,capture_output=True,text=True,timeout=45,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'})
                self.assertEqual(result.returncode,0,result.stderr)
                df=pd.read_csv(directory/'submission.csv');spec=self.keys[p['id']]
                self.assertEqual(df.columns.tolist(),['id',spec['prediction']])
                self.assertEqual(df['id'].tolist(),spec['ids'])
                pred=df[spec['prediction']]
                if spec['metric']=='roc_auc':metric=roc_auc_score(spec['y'],pred)
                elif spec['metric']=='macro_f1':metric=f1_score(spec['y'],pred,average='macro')
                else:metric=mean_squared_error(spec['y'],pred)**.5
                print(f"\n{p['id']} reference {spec['metric']}={metric:.5f} (threshold {spec['threshold']})",flush=True)
                self.assertTrue(metric>=spec['threshold'] if spec['higher'] else metric<=spec['threshold'])
                # Saved fixtures let JS evaluator parity tests use real sklearn output.
                fixtures=Path(__file__).parent/'fixtures';fixtures.mkdir(exist_ok=True)
                (fixtures/f"{p['id']}.json").write_text(json.dumps({'spec':spec,'submission':{'columns':df.columns.tolist(),'rows':df.to_dict(orient='records')},'metric':metric}))

    def test_data_is_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);generate(directory)
            for p in PROBLEMS:
                for f in p['files']:
                    self.assertEqual((directory/p['id']/f['name']).read_bytes(),(DATA/p['id']/f['name']).read_bytes())


if __name__=='__main__': unittest.main()
