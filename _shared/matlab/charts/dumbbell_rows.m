function h = dumbbell_rows(ax, a, b, labs, S, varargin)
%DUMBBELL_ROWS Two values per row joined by a bar, e.g. before and after.
%   Options: names ({'Before','After'}, written above the top row; {} to hide), fmt
p = inputParser;
addParameter(p, 'names', {'Before', 'After'}); addParameter(p, 'fmt', '%.0f');
parse(p, varargin{:}); o = p.Results; c = S.c;
a = a(:); b = b(:); n = numel(a); yv = (n:-1:1)';
lo = min([a; b]); hi = max([a; b]); pad = 0.2 * (hi - lo); dx = 0.035 * (hi - lo + 2 * pad);
style_axes(ax, S, 'x');
for r = 2:2:n
    patch(ax, [lo - pad, hi + pad, hi + pad, lo - pad], r + [-0.5 -0.5 0.5 0.5], c.grid, ...
        'EdgeColor', 'none', 'FaceAlpha', 0.55);
end
for k = 1:n
    plot(ax, [a(k) b(k)], yv(k) * [1 1], '-', 'Color', c.grey, 'LineWidth', 1.6);
    s = sign(b(k) - a(k)); if s == 0, s = 1; end
    al = {'right', 'left'};
    text(ax, b(k) + s * dx, yv(k), sprintf(o.fmt, b(k)), 'FontName', S.font, 'FontSize', S.fs.note - 0.5, ...
        'Color', c.water, 'HorizontalAlignment', al{(s > 0) + 1});
    text(ax, a(k) - s * dx, yv(k), sprintf(o.fmt, a(k)), 'FontName', S.font, 'FontSize', S.fs.note - 0.5, ...
        'Color', c.greyDark, 'HorizontalAlignment', al{(s < 0) + 1});
end
h(1) = plot(ax, a, yv, 'o', 'MarkerSize', 4.2, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', c.greyDark, 'LineWidth', 0.9);
h(2) = plot(ax, b, yv, 'o', 'MarkerSize', 4.6, 'MarkerFaceColor', c.water, 'MarkerEdgeColor', 'w', 'LineWidth', 0.5);
top = n + 0.6;
if ~isempty(o.names)
    s = sign(b(1) - a(1)); if s == 0, s = 1; end; al = {'right', 'left'}; top = n + 1.05;
    text(ax, a(1), n + 0.42, o.names{1}, 'FontName', S.font, 'FontSize', S.fs.note - 0.5, 'Color', c.greyDark, ...
        'HorizontalAlignment', al{(s < 0) + 1}, 'VerticalAlignment', 'bottom');
    text(ax, b(1), n + 0.42, o.names{2}, 'FontName', S.font, 'FontSize', S.fs.note - 0.5, 'FontWeight', 'bold', ...
        'Color', c.water, 'HorizontalAlignment', al{(s > 0) + 1}, 'VerticalAlignment', 'bottom');
end
xlim(ax, [lo - pad, hi + pad]); ylim(ax, [0.4 top]);
yticks(ax, 1:n); yticklabels(ax, flip(string(labs))); ax.YAxis.TickLength = [0 0];
end
