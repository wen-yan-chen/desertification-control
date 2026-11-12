%MAKE_PAPER_FIGURES Rebuild every MATLAB data figure used in Paper/main.tex.
%   Run from this folder:  matlab -batch make_paper_figures
%   Output: Paper/Figure/<name>.pdf (vector, used by LaTeX) and .png (preview).
%   The schematic figures (m1_structure, m1_two_clocks, m1_bucket) are TikZ
%   files in Paper/Figure; build them with pdflatex there.
fig_data_stations();     % Sec. 3   station map + observed cover
fig_m1_cover_series();   % Fig. 5a  observed cover and predictions, 7 stations
fig_m1_scenarios();      % Fig. 5b  2026-2050 scenario paths
fig_m1_water_curve();    % Fig. 6   long-run state vs irrigation
fig_m1_sensitivity();    % Fig. 7   one-at-a-time and wind sensitivity
