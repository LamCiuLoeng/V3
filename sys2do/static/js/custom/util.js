function ampm(v){
	var tmp = v.split(":");
	if(tmp.length < 2){ return v;}
	var h = parseInt(tmp[0]);
	if(h<12){ return tmp.join(":")+" AM"; }
	else if(h>23){ return  "00:00 AM";}
	else{ return (h-12)+":"+ tmp[1] + " PM" }
}