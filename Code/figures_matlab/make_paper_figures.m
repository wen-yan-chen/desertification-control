%MAKE_PAPER_FIGURES Rebuild every MATLAB data figure used in Paper/main.tex.
%   Run from this folder:  matlab -batch make_paper_figures
%   Output: Paper/Figure/<name>.pdf (vector, used by LaTeX) and .png (preview).
%   The schematic figures (m1_structure, m1_two_clocks, m1_bucket) are TikZ
%   files in Paper/Figure; build them with pdflatex there.
fig_data_stations();     % Sec. 3   station map + observed cover
fig_m1_stress_season();  % Fig. 5   K_s(M), f(T) and monthly demand
fig_m1_cover_series();   % Fig. 5a  observed cover and predictions, 7 stations
fig_m1_scenarios();      % Fig. 5b  2026-2050 scenario paths
fig_m1_water_curve();    % Fig. 6   long-run state vs irrigation
fig_m1_sensitivity();    % Fig. 7   one-at-a-time and wind sensitivity
fig_m2_plan();           % M2       15-year build schedule, spending and shares
fig_m2_cohorts();        % M2       cohort cover, quota, storage and effective area
fig_m2_water();          % M2       annual and monthly water pressure
fig_m2_tradeoff();       % M2       6 solved cost-ecology trade-off points
fig_m2_sensitivity();    % M2       investment and assumption sensitivity
fig_m2_pv_screen();      % M2       standalone PV break-even tariff and NPV
