
function close_slide(id,tid,tt)
{$('#'+id).slideToggle('slow');$(tid).toggleClass('calories_h2_table1');$('#'+tt).toggleClass('calories_total');}

function clear_calc(id)
{document.getElementById(id).reset();$("td > span").text(' ');$("td.red > div").text(' ');$("td > div.clr").text(' ');$("td > div.blood_total").text(' ');$("http://www.menshealth.com.ua/js/calc/js/td.clr1").text(' ');$("td.clr1 > div").text(' ');}
function toDot(str){return str.replace(',','.');}
