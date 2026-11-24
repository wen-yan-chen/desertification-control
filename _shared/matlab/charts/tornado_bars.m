function h = tornado_bars(ax, lo, hi, base, labs, S, varargin)
%TORNADO_BARS One-at-a-time sensitivity: output at the low and high input.
%   Rows are sorted by span, widest on top. base is the output at baseline.
%   Options: names ({'Low input','High input'}, written above the top row; {} to hide), fmt
p = inputParser;
addParameter(p, 'names', {'Low input', 'High input'}); addParameter(p, 'fmt', '%.1f');
parse(p, varargin{:}); o = p.Results; c = S.c;
lo = lo(:); hi = hi(:); n = numel(lo);
[~, ord] = sort(abs(hi - lo), 'descend');
xmin = min([lo; hi; base]); xmax = max([lo; hi; base]); pad = 0.2 * (xmax - xmin);
dx = 0.02 * (xmax - xmin + 2 * pad);
style_axes(ax, S, 'x');
for k = 1:n
    i = ord(k); y = n - k + 1;
    v = [lo(i) hi(i)]; col = [c.waterMid; c.accent];
    for q = 1:2
        h(q) = patch(ax, [base v(q) v(q) base], y + 0.3 * [-1 -1 1 1], col(q, :), 'EdgeColor', 'none'); %#ok<AGROW>
        if v(q) < base, ha = 'right'; d = -dx; else, ha = 'left'; d = dx; end
        text(ax, v(q) + d, y, sprintf(o.fmt, v(q)), 'FontName', S.font, 'FontSize', S.fs.note - 0.8, ...
            'Color', c.ink, 'HorizontalAlignment', ha);
    end
end
plot(ax, [base base], [0.4 n + 0.6], '-', 'Color', c.axis, 'LineWidth', 0.7);
top = n + 0.6;
if ~isempty(o.names)
    i = ord(1); top = n + 1.05; al = {'right', 'left'}; tc = [c.water; c.pvDark]; v = [lo(i) hi(i)];
    for q = 1:2
        text(ax, base + sign(v(q) - base) * dx, n + 0.42, o.names{q}, 'FontName', S.font, ...
            'FontSize', S.fs.note - 0.5, 'Color', tc(q, :), 'HorizontalAlignment', al{(v(q) > base) + 1}, ...
            'VerticalAlignment', 'bottom');
    end
end
xlim(ax, [xmin - pad, xmax + pad]); ylim(ax, [0.4 top]);
labs = string(labs(:)); yticks(ax, 1:n); yticklabels(ax, flip(labs(ord))); ax.YAxis.TickLength = [0 0];
end
