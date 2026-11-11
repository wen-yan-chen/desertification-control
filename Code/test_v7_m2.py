"""Economic/resource invariants, M1 carry-over, exhaustive small optimization."""
import itertools
import unittest
import numpy as np
from v7_m2_core import load_inputs, build_problem, solve, replay


class M2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c, cls.m, cls.f = load_inputs()

    def problem(self, **changes):
        return build_problem({**self.c, **changes},self.m,self.f)

    def test_full_stock_irrigation_units_and_carry(self):
        p = self.problem(years=4)
        j = next(i for i,v in enumerate(p.columns) if v["start"]==0 and v["policy"]=="constant_300")
        x = np.zeros(len(p.columns)); x[j]=1
        tab,_ = replay(p,x)
        a = tab["annual"]
        np.testing.assert_allclose(a.water_m3,150000.) # 300 mm * 50 ha * 10
        self.assertEqual(list(a.new_area_ha),[50,0,0,0])
        self.assertTrue((a.om_cny>0).all())
        cohort = tab["cohorts"]
        np.testing.assert_allclose(cohort.M_start_mm.iloc[1:],cohort.M_end_mm.iloc[:-1])
        np.testing.assert_allclose(cohort.V_start_pct.iloc[1:],cohort.V_end_pct.iloc[:-1])
        self.assertLess(abs(tab["cohort_water"].balance_residual_mm).max(),1e-8)
        np.testing.assert_allclose(tab["monthly"].groupby("year").gross_water_m3.sum(),a.water_m3)

    def test_pv_commissioning_degradation_and_cash_timing(self):
        p = self.problem(years=4)
        j = next(i for i,v in enumerate(p.columns) if v["kind"]=="pv" and v["start"]==0)
        x = np.zeros(len(p.columns)); x[j]=1
        tab,_ = replay(p,x)
        a = tab["annual"]
        self.assertEqual(a.revenue_cny.iloc[0],0)
        self.assertEqual(a.pv_facilities_cny.iloc[0],300000)
        self.assertEqual(a.pv_operating_kw.iloc[1],100)
        self.assertAlmostEqual(a.energy_kwh.iloc[2]/a.energy_kwh.iloc[1],.995)
        self.assertAlmostEqual(a.discounted_net_cost_cny.sum(),p.net_cost@x)
        self.assertAlmostEqual(a.unspent_total_budget_cny.iloc[-1],self.c["total_budget_cny"]-a.gross_spending_cny.sum())

    def test_small_milp_matches_exhaustive_feasible_enumeration(self):
        c = {**self.c,"years":3,"land_cap_ha":100.,"annual_new_area_cap_ha":50.,
             "pv_capacity_cap_kw":100.,"total_budget_cny":6000000.,"solver_relative_gap":0.,
             "min_cover_pct":0.}  # solver check only; the protection rule has its own test
        p = build_problem(c,self.m,self.f,{"constant_100":np.full(3,100.)})
        target=5.
        candidates=[]
        for values in itertools.product(*[range(int(u)+1) for u in p.variable_upper]):
            x=np.array(values,float)
            if np.max(p.A@x-p.upper)<=1e-8 and p.eco@x>=target-1e-8:
                candidates.append(p.net_cost@x)
        x,meta=solve(p,"cost",target)
        self.assertTrue(meta["feasible"])
        self.assertAlmostEqual(p.net_cost@x,min(candidates),places=5)

    def test_total_budget_and_labor_block_unfunded_actions(self):
        for changes in ({"total_budget_cny":0.},{"annual_labor_cap_person_days":0.}):
            p=self.problem(years=3,**changes)
            x,meta=solve(p,"ecology")
            self.assertTrue(meta["feasible"])
            self.assertEqual(x.sum(),0.)

    def test_monthly_cap_and_infeasible_target(self):
        p=self.problem(years=3,monthly_water_caps_m3=[0.]*12)
        x,meta=solve(p,"ecology")
        self.assertAlmostEqual(float((p.arrays["water_m3"]@x).sum()),0.)
        x,meta=solve(p,"cost",1e9)
        self.assertIsNone(x)
        self.assertEqual(meta["status"],2)

    def test_fund_shares_and_labor_not_double_charged(self):
        p=self.problem(years=3)
        j=next(i for i,v in enumerate(p.columns) if v["start"]==0 and v["policy"]=="constant_100")
        x=np.zeros(len(p.columns));x[j]=1
        tab,_=replay(p,x)
        a=tab["annual"]
        np.testing.assert_allclose(a.filter(like="fund_share").sum(axis=1),1.)
        self.assertEqual(a.labor_person_days.iloc[0],50*(30+3))
        self.assertEqual(a.gross_spending_cny.iloc[0],50*(52500+1500+100*10))

    def test_min_cover_rule_zeroes_score_but_keeps_cost_and_water(self):
        rule = dict(min_cover_pct=20.,min_cover_by_age_year=10)
        on, off = self.problem(**rule), self.problem(min_cover_pct=0.)
        self.assertEqual([c["policy"] for c in on.columns],[c["policy"] for c in off.columns])
        np.testing.assert_allclose(off.eco,off.arrays["effective_ha"].sum(axis=0))
        np.testing.assert_allclose(on.net_cost,off.net_cost)
        np.testing.assert_allclose(on.arrays["water_m3"],off.arrays["water_m3"])
        col = lambda name: next(i for i,v in enumerate(on.columns) if v["start"]==0 and v["policy"]==name)
        low, high, late = col("constant_300"), col("constant_600"), next(
            i for i,v in enumerate(on.columns) if v["start"]==12 and v["policy"]=="constant_600")
        self.assertEqual(on.eco[low],0.)                 # 15.5% at age 10: below 20%
        self.assertGreater(off.eco[low],0.)
        self.assertAlmostEqual(on.eco[high],off.eco[high])  # 21.5% at age 10: counted in full
        self.assertAlmostEqual(on.eco[late],off.eco[late])  # late batch on a qualifying path still scores
        x = np.zeros(len(on.columns)); x[low]=1; x[high]=2
        tab,_ = replay(on,x)
        a, cohorts = tab["annual"], tab["cohorts"]
        self.assertAlmostEqual(a.counted_effective_ha.sum(),on.eco@x)
        self.assertGreater(a.effective_ha.sum(),a.counted_effective_ha.sum())
        self.assertEqual(set(cohorts[cohorts.counts_toward_score].cohort_id),{"eco_y1_constant_600"})

    def test_invalid_inputs_rejected(self):
        for changes in ({"monthly_water_caps_m3":[1]*11},{"initial_M_mm":1000.},
                        {"pv_degradation_fraction_year":1.},{"pv_capex_share_min":1.1},
                        {"min_cover_pct":99.},{"min_cover_by_age_year":0}):
            with self.assertRaises(ValueError):
                self.problem(**changes)


if __name__=="__main__":
    unittest.main()
