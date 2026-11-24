function t = ink_on(col, S)
%INK_ON Text colour (ink or white) that reads on a fill colour.
if col * [0.299; 0.587; 0.114] > 0.58, t = S.c.ink; else, t = [1 1 1]; end
end
