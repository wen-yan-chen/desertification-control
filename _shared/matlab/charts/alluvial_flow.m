function alluvial_flow(ax, F, leftLabs, rightLabs, S, varargin)
%ALLUVIAL_FLOW Flows from left groups (rows of F) to right groups (columns).
%   Ribbon thickness is the flow; ribbons take the colour of their source.
%   Options: colors, gap (space between nodes as a share of the height), fmt
p = inputParser;
addParameter(p, 'colors', S.cycle); addParameter(p, 'gap', 0.035); addParameter(p, 'fmt', '%.0f');
parse(p, varargin{:}); o = p.Results; c = S.c;
[m, n] = size(F); tot = sum(F(:)); unit = (1 - (max(m, n) - 1) * o.gap) / tot; w = 0.035;
hold(ax, 'on'); axis(ax, 'off');
hL = sum(F, 2)' * unit; hR = sum(F, 1) * unit;
topL = 1 - (1 - sum(hL) - (m - 1) * o.gap) / 2 - [0 cumsum(hL(1:end - 1) + o.gap)];
topR = 1 - (1 - sum(hR) - (n - 1) * o.gap) / 2 - [0 cumsum(hR(1:end - 1) + o.gap)];
s = linspace(0, 1, 40); e = s .^ 2 .* (3 - 2 * s); xs = w + (1 - 2 * w) * s;
usedL = zeros(1, m); usedR = zeros(1, n);
for i = 1:m
    for j = 1:n
        h = F(i, j) * unit; if h <= 0, continue; end
        y0 = topL(i) - usedL(i); y1 = topR(j) - usedR(j);
        yt = y0 + (y1 - y0) * e;
        patch(ax, [xs fliplr(xs)], [yt fliplr(yt - h)], o.colors(i, :), 'FaceAlpha', 0.42, 'EdgeColor', 'none');
        usedL(i) = usedL(i) + h; usedR(j) = usedR(j) + h;
    end
end
node = @(x, yt, h, col) patch(ax, x + [0 w w 0], yt - [0 0 h h], col, 'EdgeColor', 'none');
lab = @(x, y, str, ha) text(ax, x, y, str, 'FontName', S.font, 'FontSize', S.fs.note - 0.3, ...
    'Color', c.ink, 'HorizontalAlignment', ha);
for i = 1:m
    node(0, topL(i), hL(i), o.colors(i, :));
    lab(-0.03, topL(i) - hL(i) / 2, {leftLabs{i}, ['\bf' sprintf(o.fmt, sum(F(i, :)))]}, 'right');
end
for j = 1:n
    node(1 - w, topR(j), hR(j), c.axis);
    lab(1.03, topR(j) - hR(j) / 2, {rightLabs{j}, ['\bf' sprintf(o.fmt, sum(F(:, j)))]}, 'left');
end
xlim(ax, [-0.42 1.42]); ylim(ax, [-0.02 1.02]);
end
