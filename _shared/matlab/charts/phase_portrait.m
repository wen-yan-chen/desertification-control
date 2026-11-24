function phase_portrait(ax, f, xl, yl, S, varargin)
%PHASE_PORTRAIT Direction field, nullclines and sample trajectories of a 2-D system.
%   f maps a state [x; y] to its derivative [dx; dy].
%   Options: starts (k-by-2 initial states), tmax, grid (arrows per side),
%            equilibria (k-by-2 points marked with dots)
p = inputParser;
addParameter(p, 'starts', zeros(0, 2)); addParameter(p, 'tmax', 30); addParameter(p, 'grid', 13);
addParameter(p, 'equilibria', zeros(0, 2));
parse(p, varargin{:}); o = p.Results; c = S.c;
style_axes(ax, S, 'none');
field = @(X, Y) arrayfun(@(a, b) {f([a; b])}, X, Y);
[X, Y] = meshgrid(linspace(xl(1), xl(2), o.grid), linspace(yl(1), yl(2), o.grid));
D = field(X, Y); U = cellfun(@(v) v(1), D); V = cellfun(@(v) v(2), D);
dx = diff(xl) / o.grid; dy = diff(yl) / o.grid;
L = hypot(U / dx, V / dy); L(L == 0) = 1;
quiver(ax, X, Y, 0.62 * U ./ L, 0.62 * V ./ L, 0, 'Color', c.grey, 'LineWidth', 0.5, 'MaxHeadSize', 0.9);
[Xf, Yf] = meshgrid(linspace(xl(1), xl(2), 140), linspace(yl(1), yl(2), 140));
Df = field(Xf, Yf); Uf = cellfun(@(v) v(1), Df); Vf = cellfun(@(v) v(2), Df);
contour(ax, Xf, Yf, Uf, [0 0], '--', 'Color', c.water, 'LineWidth', 0.9);
contour(ax, Xf, Yf, Vf, [0 0], '--', 'Color', c.accent, 'LineWidth', 0.9);
for k = 1:size(o.starts, 1)
    [~, z] = ode45(@(t, z) f(z), [0 o.tmax], o.starts(k, :)');
    plot(ax, z(:, 1), z(:, 2), '-', 'Color', c.plum, 'LineWidth', 1.15);
    plot(ax, z(1, 1), z(1, 2), 'o', 'MarkerSize', 3.4, 'MarkerFaceColor', 'w', 'MarkerEdgeColor', c.plum, 'LineWidth', 0.9);
    arc = [0; cumsum(hypot(diff(z(:, 1)) / dx, diff(z(:, 2)) / dy))];
    i = max(2, find(arc >= min(2.2, 0.5 * arc(end)), 1));            % arrowhead a short way along
    e = [(z(i, 1) - z(i - 1, 1)) / dx, (z(i, 2) - z(i - 1, 2)) / dy]; e = e / max(norm(e), eps); q = [-e(2) e(1)];
    tri = [0.55 * e; -0.3 * e + 0.33 * q; -0.3 * e - 0.33 * q];
    patch(ax, z(i, 1) + dx * tri(:, 1), z(i, 2) + dy * tri(:, 2), c.plum, 'EdgeColor', 'none');
end
plot(ax, o.equilibria(:, 1), o.equilibria(:, 2), 'o', 'MarkerSize', 4.4, 'MarkerFaceColor', c.ink, ...
    'MarkerEdgeColor', 'w', 'LineWidth', 0.6);
xlim(ax, xl); ylim(ax, yl);
end
