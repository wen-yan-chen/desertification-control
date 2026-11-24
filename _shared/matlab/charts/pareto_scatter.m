function front = pareto_scatter(ax, x, y, S, varargin)
%PARETO_SCATTER Candidate solutions, their non-dominated front and the chosen one.
%   Both objectives are minimised unless 'maximize' says otherwise.
%   Returns the indices of the front, sorted by x.
%   Options: maximize ([false false]), pick (index of the chosen point), picklabel
p = inputParser;
addParameter(p, 'maximize', [false false]); addParameter(p, 'pick', []); addParameter(p, 'picklabel', 'chosen');
parse(p, varargin{:}); o = p.Results; c = S.c;
x = x(:); y = y(:); P = [x y] .* (1 - 2 * o.maximize);
keep = true(numel(x), 1);
for i = 1:numel(x)
    keep(i) = ~any(all(P <= P(i, :), 2) & any(P < P(i, :), 2));
end
front = find(keep); [~, ord] = sort(x(front)); front = front(ord);
style_axes(ax, S, 'xy');
plot(ax, x(~keep), y(~keep), 'o', 'MarkerSize', 2.6, 'MarkerFaceColor', c.grey, 'MarkerEdgeColor', 'w', 'LineWidth', 0.3);
plot(ax, x(front), y(front), '-o', 'Color', c.plum, 'LineWidth', 1.1, 'MarkerSize', 3.6, ...
    'MarkerFaceColor', c.plum, 'MarkerEdgeColor', 'w');
xr = max(x) - min(x); yr = max(y) - min(y);
if ~isempty(o.pick)
    plot(ax, x(o.pick), y(o.pick), 'p', 'MarkerSize', 9.5, 'MarkerFaceColor', c.accent, ...
        'MarkerEdgeColor', c.ink, 'LineWidth', 0.6);
    ha = {'right', 'left'}; va = {'top', 'bottom'}; sgn = 1 - 2 * ~o.maximize;      % label on the open side
    text(ax, x(o.pick) + 0.04 * xr * sgn(1), y(o.pick) + 0.03 * yr * sgn(2), o.picklabel, 'FontName', S.font, ...
        'FontSize', S.fs.note - 0.3, 'FontWeight', 'bold', 'Color', c.pvDark, ...
        'HorizontalAlignment', ha{o.maximize(1) + 1}, 'VerticalAlignment', va{o.maximize(2) + 1});
end
xlim(ax, [min(x) - 0.06 * xr, max(x) + 0.06 * xr]); ylim(ax, [min(y) - 0.06 * yr, max(y) + 0.06 * yr]);
end
