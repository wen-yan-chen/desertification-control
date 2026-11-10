"""Invariant and regression tests for M1. Run: python -m unittest discover -s Code -p test_v7_m1.py"""
import unittest
import numpy as np
import pandas as pd
from dataclasses import replace
from v7_prepare_m1 import pixel_mean
from v7_m1_water import WaterParameters, water_year, vegetation_step, trajectory, equilibrium
import v7_model1 as model

class WaterTests(unittest.TestCase):
    def setUp(self):
        self.forcing = np.array([[30., 0., 100.]]*12)
        self.p = WaterParameters(rain_fraction=0.)

    def test_water_conservation_and_bounds(self):
        rng = np.random.default_rng(17)
        for _ in range(50):
            rain = rng.uniform(0,100,(12,))
            f = self.forcing.copy(); f[:,1] = rain
            p = replace(self.p, rain_fraction=.5)
            end, w, rows = water_year(rng.uniform(0,38),rng.uniform(0,75),rng.uniform(0,2000),f,p)
            self.assertTrue(0 <= end <= 75 and 0 <= w <= 1)
            self.assertLess(max(abs(x['balance_residual_mm']) for x in rows),1e-8)

    def test_no_water_uses_storage_then_declines(self):
        end,w,_ = water_year(20.,0.,0.,self.forcing,self.p)
        self.assertEqual((end,w),(0.,0.))
        end,w,_ = water_year(20.,75.,0.,self.forcing,self.p)
        self.assertGreater(w,0)
        self.assertLess(end,75.)
        self.assertAlmostEqual(vegetation_step(20,40,0,1,.6,.1),18.)

    def test_zero_cover_is_absorbing_without_planting(self):
        a,_=trajectory(0.,37.5,5,40,.6,.1,self.forcing,1000,self.p)
        self.assertTrue((a.V_end_pct == 0).all())

    def test_invalid_input_not_silently_clipped(self):
        with self.assertRaises(ValueError):
            vegetation_step(41,40,1,1,.6,.1)
        with self.assertRaises(ValueError):
            vegetation_step(20,40,1,3,.6,.9,.1)
        with self.assertRaises(ValueError):
            water_year(20,20,-1,self.forcing)

    def test_more_water_cannot_reduce_equilibrium_base_case(self):
        values=[equilibrium(2,37.5,40,.6,.1,self.forcing,q,self.p) for q in (0,100,300,600)]
        self.assertTrue(all(x['converged'] for x in values))
        self.assertTrue(np.all(np.diff([x['V_pct'] for x in values])>=-1e-6))

    def test_explicit_censoring_and_terminal_state(self):
        z=equilibrium(2,37.5,40,.6,.1,self.forcing,300,self.p,max_years=1)
        self.assertFalse(z['converged'])
        a,m=trajectory(2,37.5,25,40,.6,.1,self.forcing,300,self.p)
        self.assertEqual((len(a),len(m),int(a.iloc[-1].year)),(25,300,25))
        self.assertAlmostEqual(a.iloc[-1].M_end_mm,m.iloc[-1].M_end_mm)
        self.assertAlmostEqual(a.iloc[1].V_start_pct,a.iloc[0].V_end_pct)

class DataTests(unittest.TestCase):
    def test_pixel_qa_not_window_median(self):
        mean,n = pixel_mean([2000,4000,10000,-3000],[0,1,3,-1])
        self.assertEqual(n,2)
        self.assertAlmostEqual(mean,.3)
        self.assertTrue(np.isnan(pixel_mean([2000,9000,9000],[0,3,3])[0]))

    def test_free_cohort_parameters_are_degenerate(self):
        v=np.array([2.,10.,20.])
        # Same r-d and r/K => exactly the same dynamics, despite different r,d,K.
        np.testing.assert_allclose(model.step(v,40,1,1,.6,.1),model.step(v,60,1,1,.9,.4))

    def test_future_observations_do_not_change_fit(self):
        _,a=model.yearly_table()
        fit,th,_=model.fit_stations(a)
        b=a.copy()
        b.loc[b.year>2022,'V']*=1.5
        b['V_next']=b.groupby('site').V.shift(-1)
        fit2,th2,_=model.fit_stations(b)
        np.testing.assert_allclose(th,th2,rtol=0,atol=1e-12)
        self.assertEqual(fit['baselines']['eligible_sites'],fit2['baselines']['eligible_sites'])

if __name__ == '__main__':
    unittest.main()
