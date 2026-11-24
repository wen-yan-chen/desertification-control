%MAKE_MORE_FIGURES Same-style Model 2 figures that were cut from the final paper.
%   Run from this folder:  matlab -batch make_more_figures
%   Kept as templates for chart types the paper does not use: cost-benefit
%   points, break-even screening, a month-by-year heatmap and stacked cohorts.
addpath(fullfile(fileparts(mfilename('fullpath')), '..'));
fig_m2_tradeoff();       % solved cost-ecology points with side panels
fig_m2_sensitivity();    % lollipop rows + bars across 14 scenarios
fig_m2_pv_screen();      % break-even tariff (log axis) and signed NPV bars
fig_m2_water();          % bars against a cap, monthly lines, heatmap
fig_m2_cohorts();        % stacked small panels sharing one x axis
