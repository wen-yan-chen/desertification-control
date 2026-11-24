function waterfall_bars(ax, start, deltas, labs, S, varargin)
%WATERFALL_BARS From a starting total through signed changes to a final total.
%   labs names the start, each change and the end: numel(deltas) + 2 entries.
%   Options: fmt (totals), dfmt (changes)
p = inputParser;
addParameter(p, 'fmt', '%.1f'); addParameter(p, 'dfmt', '%+.1f');
parse(p, varargin{:}); o = p.Results; c = S.c;
d = deltas(:)'; lev = start + [0 cumsum(d)]; n = numel(d) + 2;
style_axes(ax, S, 'y');
rngv = max(lev) - min([0 lev]);
bar1 = @(x, y0, y1, col) patch(ax, x + 0.34 * [-1 1 1 -1], [y0 y0 y1 y1], col, 'EdgeColor', 'none');
lab1 = @(x, y, s, va) text(ax, x, y, s, 'FontName', S.font, 'FontSize', S.fs.note - 0.8, ...
    'Color', c.ink, 'HorizontalAlignment', 'center', 'VerticalAlignment', va);
bar1(1, 0, lev(1), c.water); lab1(1, lev(1), sprintf(o.fmt, lev(1)), 'bottom');
for k = 1:numel(d)
    col = c.accent; if d(k) < 0, col = c.waterMid; end
    bar1(k + 1, lev(k), lev(k + 1), col);
    plot(ax, k + [0.34 0.66], lev(k) * [1 1], '-', 'Color', c.grey, 'LineWidth', 0.6);
    lab1(k + 1, max(lev(k), lev(k + 1)), sprintf(o.dfmt, d(k)), 'bottom');
end
plot(ax, n - 1 + [0.34 0.66], lev(end) * [1 1], '-', 'Color', c.grey, 'LineWidth', 0.6);
bar1(n, 0, lev(end), c.water); lab1(n, lev(end), sprintf(o.fmt, lev(end)), 'bottom');
xlim(ax, [0.45 n + 0.55]); ylim(ax, [min([0 lev]) max(lev) + 0.14 * rngv]);
xticks(ax, 1:n); xticklabels(ax, labs); ax.XAxis.TickLength = [0 0];
end
