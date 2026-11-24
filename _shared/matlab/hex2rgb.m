function c = hex2rgb(hex)
%HEX2RGB '1E5F74' or '#1E5F74' -> [r g b] in 0..1.
hex = char(hex);
hex = hex(end-5:end);
c = [hex2dec(hex(1:2)) hex2dec(hex(3:4)) hex2dec(hex(5:6))] / 255;
end
