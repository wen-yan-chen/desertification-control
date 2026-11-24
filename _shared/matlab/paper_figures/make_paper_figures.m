%MAKE_PAPER_FIGURES Rebuild the ten MATLAB figures of the final paper.
%   Run from this folder:  matlab -batch make_paper_figures
%   Reads the frozen tables under <project>/Results/v7 and <project>/Data/v7
%   (see paper_style for how the project folder is found) and writes
%   <name>.pdf and <name>.png to MCM_FIG_OUT, or ./figures if it is unset.
addpath(fullfile(fileparts(mfilename('fullpath')), '..'));
fig_intro_factors();     % Fig. 1   management factors on shelterbelt photos
fig_data_stations();     % Fig. 3   station map + observed cover
fig_m1_stress_season();  % Fig. 7   K_s(M), f(T) and monthly demand
fig_m1_cover_series();   % Fig. 8a  observed cover and predictions, 7 stations
fig_m1_scenarios();      % Fig. 8b  2026-2050 scenario paths
fig_m1_water_curve();    % Fig. 9   long-run state vs irrigation
fig_m1_sensitivity();    % Fig. 10  one-at-a-time and wind sensitivity
fig_m2_plan();           % Fig. 13  15-year build schedule, spending and shares
fig_m3_resilience();     % Fig. 15  cohort paths, recovery, risk and canal rationing
fig_m3_sensitivity_val();% Fig. 16  3-D storm grid and mechanism contrasts
