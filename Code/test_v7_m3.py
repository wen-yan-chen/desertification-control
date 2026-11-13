import copy
import unittest
import numpy as np
from v7_m1_water import water_year,vegetation_step,WaterParameters
from v7_m3_core import (load_inputs,batch_year,allocation,storm_draw,compound_nodes,
    simulate,stationary_chain,wilson,validate)


class M3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c,cls.m,cls.m2,cls.coh,cls.f,cls.replay_error=load_inputs()

    def test_m2_terminal_states_match_current_m1(self):
        self.assertLess(self.replay_error,1e-5)

    def test_vectorized_bucket_matches_scalar_m1(self):
        rng=np.random.default_rng(77);v=rng.uniform(0,self.m['K_section_pct'],15);m=rng.uniform(0,75,15)
        quotas=rng.uniform(0,1000,15);gross=quotas[:,None]*self.f[:,2]/self.f[:,2].sum()
        vv,mm,w,err=batch_year(v,m,self.f,gross,self.m)
        for i in range(len(v)):
            ms,ws,_=water_year(v[i],m[i],quotas[i],self.f,WaterParameters(**self.m['water']))
            vs=vegetation_step(v[i],self.m['K_section_pct'],ws,self.m['r'],self.m['d'])
            self.assertAlmostEqual(vv[i],vs,places=10);self.assertAlmostEqual(mm[i],ms,places=10)
        self.assertLess(err,1e-8)

    def test_monthly_rationing_and_annual_cap(self):
        c={**self.c,'irrigation_multiplier':10.,'drought_supply_multiplier':.1}
        _,a=allocation(c,self.m2,self.coh,self.f,True)
        self.assertTrue((a['total_m3']<=a['cap_m3']+1e-8).all())
        self.assertLessEqual(a['total_m3'].sum(),a['annual_cap_m3']+1e-8)
        self.assertTrue((a['delivered_eco_m3']<a['requested_eco_m3']).any())

    def test_compound_poisson_moments_not_bernoulli(self):
        rng=np.random.default_rng(11);lam=1.4;lo=.1;hi=.5
        r,n=storm_draw(rng,np.full(150000,lam),lo,hi)
        target=np.exp(-lam*(lo+hi)/2)
        self.assertAlmostEqual(r.mean(),target,delta=.003)
        self.assertGreater((n>=2).mean(),.3)
        rr,ww,d=compound_nodes(lam,lo,hi,192)
        self.assertAlmostEqual(ww.sum(),1.);self.assertAlmostEqual(rr@ww,target,delta=.001)
        self.assertLess(d['tail_mass'],1e-11)

    def test_no_storm_does_not_mean_no_failure(self):
        c={**self.c,'horizon_years':20,'paths':5,'storm_rate_per_year':0.,'drought_probability':0.,
           'drought_probability_increment':0.,'irrigation_multiplier':0.,'wind_log_trend_per_year':0.,
           'rain_log_trend_per_year':0.,'storm_rate_log_trend_per_year':0.}
        tab,_=simulate(c,self.m,self.m2,self.coh,self.f,np.ones((20,12)),paths=5)
        self.assertTrue((tab['summary'].p_failure==1.).all())
        self.assertTrue((tab['cohort_annual'].groupby('cohort_id').failure_probability.diff().dropna()>=0).all())

    def test_censoring_and_wilson_boundary(self):
        c={**self.c,'horizon_years':2,'paths':3,'storm_rate_per_year':0.,'drought_probability':0.,'drought_probability_increment':0.}
        tab,_=simulate(c,self.m,self.m2,self.coh,self.f,np.ones((2,12)),paths=3)
        self.assertTrue((tab['summary'].censored_count==3).all())
        self.assertTrue((tab['summary'].restricted_mean_first_passage_years==2.).all())
        lo,hi=wilson(0,3);self.assertEqual(lo,0.);self.assertGreater(hi,0.)

    def test_initial_failure_is_time_zero(self):
        coh=self.coh.copy();coh['V_end_pct']=1.
        c={**self.c,'horizon_years':1,'paths':3}
        tab,_=simulate(c,self.m,self.m2,coh,self.f,np.ones((1,12)),paths=3)
        self.assertTrue((tab['first_passage_counts'].query('first_failure_year == 0')['count']==3).all())

    def test_chain_orientation_and_mc_validation(self):
        c={**self.c,'horizon_years':5,'paths':6000,'wind_log_trend_per_year':0.,'rain_log_trend_per_year':0.,
           'storm_rate_log_trend_per_year':0.,'drought_probability_increment':0.}
        tab,_=simulate(c,self.m,self.m2,self.coh,self.f,np.ones((5,12)))
        chain,diag=stationary_chain(c,self.m,self.m2,self.coh,self.f,0,81,11,48)
        mc=tab['summary'].iloc[0]
        self.assertLess(abs(chain.failure_probability.iloc[-1]-mc.p_failure),.025)
        self.assertTrue((chain.failure_probability.diff().dropna()>=-1e-10).all())
        self.assertLessEqual(diag['max_row_sum'],1+1e-10)
        self.assertGreater(diag['expected_first_passage_years'],0.)

    def test_invalid_trend_probabilities_rejected(self):
        with self.assertRaises(ValueError):validate({**self.c,'drought_probability_increment':.1},self.m)
        with self.assertRaises(ValueError):validate({**self.c,'storm_loss_high':1.},self.m)


if __name__=='__main__':unittest.main()
