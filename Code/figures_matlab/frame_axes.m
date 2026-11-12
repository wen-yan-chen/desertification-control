function frame_axes(ax, S)
%FRAME_AXES Thin closed frame without top/right ticks (阿昆 template).
%   MATLAB mirrors the ticks when Box is on, so the frame is drawn as a line
%   on the axis limits instead. Also sets true minus signs on numeric tick
%   labels. Call it last, after the limits and ticks are final.
xl = xlim(ax); yl = ylim(ax);
ax.XLimMode = 'manual'; ax.YLimMode = 'manual';
plot(ax, xl([1 2 2 1 1]), yl([1 1 2 2 1]), '-', 'Color', S.c.axis, ...
    'LineWidth', 0.6, 'Clipping', 'off', 'HandleVisibility', 'off');
ax.XTickLabel = true_minus(ax.XTickLabel);
ax.YTickLabel = true_minus(ax.YTickLabel);
end

function lab = true_minus(lab)
if isempty(lab), return; end
lab = regexprep(cellstr(lab), '^-(?=\d)', char(8722));
end
