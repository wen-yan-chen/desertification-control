function h = interval_rows(ax, est, lo, hi, labs, S, varargin)
%INTERVAL_ROWS Point estimates against a reference interval, one row per case.
%   est is n-by-k (k estimators, k <= 3); lo and hi bound the interval.
%   Options: ref (vertical reference line, [] to hide), names (interval first,
%            then one per estimator; drawn in a reserved strip at the bottom),
%            ncol (legend columns, default 2)
p = inputParser;
addParameter(p, 'ref', 0); addParameter(p, 'names', {}); addParameter(p, 'ncol', []);
parse(p, varargin{:}); o = p.Results; c = S.c;
[n, k] = size(est); yv = (n:-1:1)';
mk = {'o', 'd', 's'}; col = [c.water; c.accent; c.plum];
off = 0.17 * ((1:k) - (k + 1) / 2);
xmin = min([lo(:); est(:)]); xmax = max([hi(:); est(:)]); pad = 0.08 * (xmax - xmin);
style_axes(ax, S, 'x');
for i = 1:n
    h(1) = patch(ax, [lo(i) hi(i) hi(i) lo(i)], yv(i) + 0.3 * [-1 -1 1 1], c.waterLight, 'EdgeColor', 'none'); %#ok<AGROW>
end
if ~isempty(o.ref)
    plot(ax, [o.ref o.ref], [0.4 n + 0.6], '-', 'Color', c.greyDark, 'LineWidth', 0.7);
end
for j = 1:k
    h(j + 1) = plot(ax, est(:, j), yv - off(j), mk{j}, 'MarkerSize', 4, 'MarkerFaceColor', col(j, :), ...
        'MarkerEdgeColor', 'w', 'LineWidth', 0.45); %#ok<AGROW>
end
if isempty(o.ncol), o.ncol = 2; end
bot = 0.4; if ~isempty(o.names), bot = 0.05 - 0.75 * ceil((k + 1) / o.ncol); end   % room for the legend
xlim(ax, [xmin - pad, xmax + pad]); ylim(ax, [bot n + 0.6]);
yticks(ax, 1:n); yticklabels(ax, flip(string(labs))); ax.YAxis.TickLength = [0 0];
ax.XTickLabelRotation = 0;
if ~isempty(o.names), kit_legend(ax, h, o.names, S, 'south', o.ncol); end
end
