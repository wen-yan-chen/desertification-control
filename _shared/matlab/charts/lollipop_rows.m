function lollipop_rows(ax, vals, labs, base, S, varargin)
%LOLLIPOP_ROWS One row per case: a stem from the baseline to a labelled dot.
%   lollipop_rows(ax, vals, labs, base, S, 'colors', C, 'highlight', k, ...)
%   vals(k) and labs(k) are listed top to bottom. The baseline is a dashed
%   vertical line; values sit on the far side of each dot.
%   Options
%     colors     n-by-3 dot colours, default plum for every row
%     highlight  row index given a tinted band and a bold label (the baseline case)
%     xlim       x limits, default padded data range
%     fmt        number format, default '%.1f'
p = inputParser;
addParameter(p, 'colors', []);
addParameter(p, 'highlight', []);
addParameter(p, 'xlim', []);
addParameter(p, 'fmt', '%.1f');
parse(p, varargin{:});
o = p.Results; c = S.c;
vals = vals(:); labs = string(labs(:)); n = numel(vals);
if isempty(o.colors), o.colors = repmat(c.plum, n, 1); end
if isempty(o.xlim)
    lo = min([vals; base]); hi = max([vals; base]); pad = 0.16 * (hi - lo);
    o.xlim = [lo - pad, hi + pad];
end
yv = (n:-1:1)';
dx = 0.025 * diff(o.xlim);

style_axes(ax, S, 'x');
for r = 2:2:n
    patch(ax, o.xlim([1 2 2 1]), r + [-0.5 -0.5 0.5 0.5], c.grid, ...
        'EdgeColor', 'none', 'FaceAlpha', 0.55, 'HandleVisibility', 'off');
end
if ~isempty(o.highlight)
    patch(ax, o.xlim([1 2 2 1]), yv(o.highlight) + [-0.5 -0.5 0.5 0.5], c.waterLight, ...
        'EdgeColor', 'none', 'FaceAlpha', 0.9, 'HandleVisibility', 'off');
    labs(o.highlight) = sprintf('\\color[rgb]{%.3f,%.3f,%.3f}\\bf%s', c.water, labs(o.highlight));
end
xline(ax, base, '--', 'Color', c.greyDark, 'LineWidth', 0.85, 'HandleVisibility', 'off');
for k = 1:n
    plot(ax, [base vals(k)], [yv(k) yv(k)], '-', 'Color', c.grey, 'LineWidth', 1.25, 'HandleVisibility', 'off');
    plot(ax, vals(k), yv(k), 'o', 'MarkerSize', 4.0, 'MarkerFaceColor', o.colors(k, :), ...
        'MarkerEdgeColor', 'w', 'LineWidth', 0.45, 'HandleVisibility', 'off');
    d = dx; ha = 'left';
    if vals(k) < base, d = -dx; ha = 'right'; end
    text(ax, vals(k) + d, yv(k), sprintf(o.fmt, vals(k)), 'FontName', S.font, ...
        'FontSize', S.fs.note - 0.5, 'Color', c.ink, 'HorizontalAlignment', ha);
end
xlim(ax, o.xlim); ylim(ax, [0.4 n + 0.6]);
yticks(ax, 1:n); yticklabels(ax, flip(labs));
ax.YAxis.TickLength = [0 0]; ax.YAxis.FontSize = S.fs.note - 0.5;
end
